from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from models.user import User
from models.models import Job, Resume, Application, AuditLog
from ml.scorer import extract_text_from_pdf, compute_final_score, apply_shortlisting
from datetime import datetime
import os, zipfile, io

recruiter_bp = Blueprint('recruiter', __name__)
ALLOWED_EXT = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def get_recruiter():
    uid = get_jwt_identity()
    user = User.query.get(int(uid))
    if not user or user.role not in ['recruiter', 'admin']:
        return None
    return user

def log(uid, action, details=''):
    db.session.add(AuditLog(user_id=uid, action=action, details=details,
                             ip_address=request.remote_addr))
    db.session.commit()


# ─── Jobs ──────────────────────────────────────────────────────────────────

@recruiter_bp.route('/jobs', methods=['GET'])
@jwt_required()
def list_jobs():
    rec = get_recruiter()
    if not rec: return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    jobs = Job.query.filter_by(recruiter_id=rec.id).order_by(Job.created_at.desc()).all()
    return jsonify({'success': True, 'jobs': [j.to_dict() for j in jobs]})


@recruiter_bp.route('/jobs', methods=['POST'])
@jwt_required()
def create_job():
    rec = get_recruiter()
    if not rec: return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.get_json()
    required = ['title', 'description', 'skills_required']
    for f in required:
        if not data.get(f):
            return jsonify({'success': False, 'message': f'{f} is required'}), 400

    job = Job(
        title=data['title'],
        description=data['description'],
        skills_required=data['skills_required'],
        experience_required=data.get('experience_required', ''),
        location=data.get('location', ''),
        job_type=data.get('job_type', 'Full-time'),
        recruiter_id=rec.id
    )
    db.session.add(job)
    db.session.commit()
    log(rec.id, 'CREATE_JOB', f'Job: {job.title} (ID:{job.id})')
    return jsonify({'success': True, 'message': 'Job created', 'job': job.to_dict()})


@recruiter_bp.route('/jobs/<int:jid>', methods=['PUT'])
@jwt_required()
def update_job(jid):
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    job = Job.query.filter_by(id=jid, recruiter_id=rec.id).first()
    if not job: return jsonify({'success': False, 'message': 'Job not found'}), 404
    data = request.get_json()
    for field in ['title', 'description', 'skills_required', 'experience_required', 'location', 'job_type', 'status']:
        if field in data:
            setattr(job, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Job updated', 'job': job.to_dict()})


@recruiter_bp.route('/jobs/<int:jid>', methods=['DELETE'])
@jwt_required()
def delete_job(jid):
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    job = Job.query.filter_by(id=jid, recruiter_id=rec.id).first()
    if not job: return jsonify({'success': False}), 404
    db.session.delete(job)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Job deleted'})


# ─── Resume Upload & Scoring ───────────────────────────────────────────────

@recruiter_bp.route('/jobs/<int:jid>/upload-resumes', methods=['POST'])
@jwt_required()
def upload_resumes(jid):
    """
    Recruiter uploads multiple resumes for a job.
    Creates guest candidate accounts if email not registered.
    Triggers AI scoring immediately.
    """
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    job = Job.query.filter_by(id=jid, recruiter_id=rec.id).first()
    if not job: return jsonify({'success': False, 'message': 'Job not found'}), 404

    files = request.files.getlist('resumes')
    if not files:
        return jsonify({'success': False, 'message': 'No files uploaded'}), 400

    results = []
    upload_dir = current_app.config['UPLOAD_FOLDER']

    for file in files:
        if not allowed_file(file.filename):
            results.append({'filename': file.filename, 'error': 'Not a PDF'})
            continue

        filename = secure_filename(file.filename)
        unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(upload_dir, unique_name)
        file.save(filepath)

        # Extract text
        resume_text = extract_text_from_pdf(filepath)

        # Create a guest candidate from filename (no login needed for bulk upload)
        email_guess = filename.replace('.pdf', '').replace(' ', '_').lower() + '@upload.local'
        candidate = User.query.filter_by(email=email_guess).first()
        if not candidate:
            from werkzeug.security import generate_password_hash
            candidate = User(
                name=filename.replace('.pdf', ''),
                email=email_guess,
                password=generate_password_hash('temp_pass'),
                role='candidate',
                is_verified=True,
                is_active=True
            )
            db.session.add(candidate)
            db.session.flush()

        # Save resume
        resume = Resume(
            candidate_id=candidate.id,
            filename=filename,
            filepath=filepath,
            extracted_text=resume_text
        )
        db.session.add(resume)
        db.session.flush()

        # Score
        job_text = f"{job.title} {job.description} {job.skills_required}"
        scores = compute_final_score(resume_text, job_text)

        # Check duplicate application
        existing = Application.query.filter_by(job_id=jid, resume_id=resume.id).first()
        if not existing:
            app = Application(
                job_id=jid,
                candidate_id=candidate.id,
                resume_id=resume.id,
                tfidf_score=scores['tfidf_score'],
                bert_score=scores['bert_score'],
                final_score=scores['final_score'],
                match_percentage=scores['match_percentage'],
                status='pending',
                scored_at=datetime.utcnow()
            )
            db.session.add(app)

        results.append({
            'filename': filename,
            'candidate': candidate.name,
            'tfidf_score': scores['tfidf_score'],
            'bert_score': scores['bert_score'],
            'final_score': scores['final_score'],
            'match_percentage': scores['match_percentage']
        })

    db.session.commit()

    # Auto-shortlist
    apps = Application.query.filter_by(job_id=jid).all()
    ranked = apply_shortlisting(apps)
    db.session.commit()

    log(rec.id, 'UPLOAD_RESUMES', f'{len(files)} resumes for Job {jid}')
    return jsonify({'success': True, 'results': results, 'total': len(results)})


@recruiter_bp.route('/jobs/<int:jid>/results', methods=['GET'])
@jwt_required()
def job_results(jid):
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    apps = Application.query.filter_by(job_id=jid).order_by(Application.final_score.desc()).all()
    return jsonify({'success': True, 'applications': [a.to_dict() for a in apps]})


@recruiter_bp.route('/jobs/<int:jid>/shortlist', methods=['POST'])
@jwt_required()
def manual_shortlist(jid):
    """Re-run shortlisting with a custom threshold."""
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    data = request.get_json()
    threshold = data.get('threshold', 50.0)
    apps = Application.query.filter_by(job_id=jid).all()
    ranked = apply_shortlisting(apps, threshold)
    db.session.commit()
    shortlisted = sum(1 for a in ranked if a.status == 'shortlisted')
    return jsonify({'success': True, 'shortlisted': shortlisted, 'total': len(ranked)})


@recruiter_bp.route('/jobs/<int:jid>/download-shortlist', methods=['GET'])
@jwt_required()
def download_shortlist(jid):
    """Download a ZIP of all shortlisted resumes for a job."""
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    apps = Application.query.filter_by(job_id=jid, status='shortlisted').all()
    if not apps:
        return jsonify({'success': False, 'message': 'No shortlisted candidates'}), 404

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for a in apps:
            if a.resume and os.path.exists(a.resume.filepath):
                zf.write(a.resume.filepath, a.resume.filename)
    zip_buffer.seek(0)

    job = Job.query.get(jid)
    log(rec.id, 'DOWNLOAD_SHORTLIST', f'Job {jid} - {len(apps)} resumes')
    return send_file(zip_buffer, mimetype='application/zip',
                     download_name=f'shortlisted_{job.title.replace(" ","_")}.zip',
                     as_attachment=True)


@recruiter_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    rec = get_recruiter()
    if not rec: return jsonify({'success': False}), 403
    total_jobs = Job.query.filter_by(recruiter_id=rec.id).count()
    open_jobs = Job.query.filter_by(recruiter_id=rec.id, status='open').count()
    job_ids = [j.id for j in Job.query.filter_by(recruiter_id=rec.id).all()]
    total_apps = Application.query.filter(Application.job_id.in_(job_ids)).count()
    shortlisted = Application.query.filter(Application.job_id.in_(job_ids), Application.status=='shortlisted').count()
    return jsonify({'success': True, 'stats': {
        'total_jobs': total_jobs, 'open_jobs': open_jobs,
        'total_applications': total_apps, 'shortlisted': shortlisted
    }})
