from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.user import User
from models.models import Job, Application, AuditLog, Resume

admin_bp = Blueprint('admin', __name__)

def require_admin():
    uid = get_jwt_identity()
    user = User.query.get(int(uid))
    if not user or user.role != 'admin':
        return None, jsonify({'success': False, 'message': 'Admin access required'}), 403
    return user, None, None

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, err, code = require_admin()
    if err: return err, code

    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()
    shortlisted = Application.query.filter_by(status='shortlisted').count()
    recruiters = User.query.filter_by(role='recruiter').count()
    candidates = User.query.filter_by(role='candidate').count()

    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'shortlisted': shortlisted,
            'recruiters': recruiters,
            'candidates': candidates
        }
    })


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    user, err, code = require_admin()
    if err: return err, code
    role = request.args.get('role')
    query = User.query
    if role:
        query = query.filter_by(role=role)
    users = query.order_by(User.created_at.desc()).all()
    return jsonify({'success': True, 'users': [u.to_dict() for u in users]})


@admin_bp.route('/users/<int:uid>/toggle', methods=['POST'])
@jwt_required()
def toggle_user(uid):
    user, err, code = require_admin()
    if err: return err, code
    target = User.query.get(uid)
    if not target:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    target.is_active = not target.is_active
    db.session.commit()
    action = 'ACTIVATE' if target.is_active else 'DEACTIVATE'
    log = AuditLog(user_id=int(get_jwt_identity()), action=f'ADMIN_{action}_USER',
                   details=f'User {target.email}', ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True, 'is_active': target.is_active})


@admin_bp.route('/users/<int:uid>', methods=['DELETE'])
@jwt_required()
def delete_user(uid):
    user, err, code = require_admin()
    if err: return err, code
    target = User.query.get(uid)
    if not target:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    email = target.email
    db.session.delete(target)
    db.session.commit()
    log = AuditLog(user_id=int(get_jwt_identity()), action='ADMIN_DELETE_USER',
                   details=f'Deleted user {email}', ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted'})


@admin_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_jobs():
    user, err, code = require_admin()
    if err: return err, code
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return jsonify({'success': True, 'jobs': [j.to_dict() for j in jobs]})


@admin_bp.route('/jobs/<int:jid>', methods=['DELETE'])
@jwt_required()
def delete_job(jid):
    user, err, code = require_admin()
    if err: return err, code
    job = Job.query.get(jid)
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    db.session.delete(job)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Job deleted'})


@admin_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    user, err, code = require_admin()
    if err: return err, code
    apps = Application.query.order_by(Application.applied_at.desc()).all()
    return jsonify({'success': True, 'applications': [a.to_dict() for a in apps]})


@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    user, err, code = require_admin()
    if err: return err, code
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=50)
    return jsonify({
        'success': True,
        'logs': [l.to_dict() for l in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    })


@admin_bp.route('/promote', methods=['POST'])
@jwt_required()
def promote_user():
    user, err, code = require_admin()
    if err: return err, code
    data = request.get_json()
    uid = data.get('user_id')
    new_role = data.get('role')
    if new_role not in ['candidate', 'recruiter', 'admin']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400
    target = User.query.get(uid)
    if not target:
        return jsonify({'success': False}), 404
    target.role = new_role
    db.session.commit()
    return jsonify({'success': True, 'message': f'User promoted to {new_role}'})
# -----------------------------
# Admin Analytics for Charts
# -----------------------------

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def analytics():

    user, err, code = require_admin()
    if err:
        return err, code

    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()

    shortlisted = Application.query.filter_by(status='shortlisted').count()

    recruiters = User.query.filter_by(role='recruiter').count()
    candidates = User.query.filter_by(role='candidate').count()

    return jsonify({
        "success": True,
        "stats": {
            "users": total_users,
            "jobs": total_jobs,
            "applications": total_applications,
            "shortlisted": shortlisted,
            "recruiters": recruiters,
            "candidates": candidates
        }
    })


# -----------------------------
# Applications Per Job Graph
# -----------------------------

@admin_bp.route('/job-analytics', methods=['GET'])
@jwt_required()
def job_analytics():

    user, err, code = require_admin()
    if err:
        return err, code

    jobs = Job.query.all()

    data = []

    for job in jobs:

        count = Application.query.filter_by(job_id=job.id).count()

        data.append({
            "job_title": job.title,
            "applications": count
        })

    return jsonify({
        "success": True,
        "jobs": data
    })


# -----------------------------
# Top Candidates Ranking
# -----------------------------

@admin_bp.route('/top-candidates', methods=['GET'])
@jwt_required()
def top_candidates():

    user, err, code = require_admin()
    if err:
        return err, code

    apps = Application.query.order_by(Application.final_score.desc()).limit(10).all()

    results = []

    for a in apps:

        user = User.query.get(a.candidate_id)

        results.append({
            "candidate": user.name if user else "Unknown",
            "email": user.email if user else "",
            "score": a.match_percentage,
            "job_id": a.job_id
        })

    return jsonify({
        "success": True,
        "top_candidates": results
    })


# -----------------------------
# Resume Skill Distribution
# -----------------------------

@admin_bp.route('/skill-analytics', methods=['GET'])
@jwt_required()
def skill_analytics():

    user, err, code = require_admin()
    if err:
        return err, code

    resumes = Resume.query.all()

    skill_counts = {}

    from ml.scorer import extract_skills

    for r in resumes:

        skills = extract_skills(r.extracted_text or "")

        for s in skills:

            skill_counts[s] = skill_counts.get(s, 0) + 1

    return jsonify({
        "success": True,
        "skills": skill_counts
    })