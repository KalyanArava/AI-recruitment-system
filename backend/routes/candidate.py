from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import traceback

from app import db
from models.user import User
from models.models import Job, Resume, Application, AuditLog
from backend.ml.scorer import extract_text_from_pdf, compute_final_score, extract_skills

candidate_bp = Blueprint("candidate", __name__)

ALLOWED_EXT = {"pdf"}


# -----------------------------
# Helper Functions
# -----------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def get_candidate():
    uid = get_jwt_identity()
    return User.query.get(int(uid))


def log_action(uid, action, details=""):
    try:
        log = AuditLog(
            user_id=uid,
            action=action,
            details=details,
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


# -----------------------------
# List Jobs
# -----------------------------

@candidate_bp.route("/jobs", methods=["GET"])
@jwt_required()
def list_open_jobs():

    jobs = Job.query.filter_by(status="open") \
        .order_by(Job.created_at.desc()).all()

    return jsonify({
        "success": True,
        "jobs": [j.to_dict() for j in jobs]
    })


# -----------------------------
# Upload Resume
# -----------------------------

@candidate_bp.route("/upload-resume", methods=["POST"])
@jwt_required()
def upload_resume():

    try:

        cand = get_candidate()
        if not cand:
            return jsonify({"success": False, "message": "User not found"}), 403

        if "resume" not in request.files:
            return jsonify({"success": False, "message": "No file uploaded"}), 400

        file = request.files["resume"]

        if file.filename == "":
            return jsonify({"success": False, "message": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "message": "Only PDF files allowed"}), 400

        filename = secure_filename(file.filename)

        unique_name = f"{cand.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]

        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, unique_name)

        file.save(filepath)

        print("Saved resume:", filepath)

        # Extract text safely
        try:
            text = extract_text_from_pdf(filepath)
        except Exception:
            text = ""

        skills = extract_skills(text) if text else []

        resume = Resume(
            candidate_id=cand.id,
            filename=filename,
            filepath=filepath,
            extracted_text=text,
        )

        db.session.add(resume)
        db.session.commit()

        log_action(cand.id, "UPLOAD_RESUME", filename)

        return jsonify({
            "success": True,
            "resume": resume.to_dict(),
            "extracted_skills": skills,
            "preview": text[:400] if text else ""
        })

    except Exception as e:

        db.session.rollback()

        print("[UPLOAD ERROR]")
        print(traceback.format_exc())

        return jsonify({
            "success": False,
            "message": "Resume upload failed"
        }), 500


# -----------------------------
# Apply to Job
# -----------------------------

@candidate_bp.route("/apply/<int:jid>", methods=["POST"])
@jwt_required()
def apply_to_job(jid):

    try:

        cand = get_candidate()

        if not cand:
            return jsonify({"success": False}), 403

        data = request.get_json() or {}

        resume_id = data.get("resume_id")

        if not resume_id:
            return jsonify({
                "success": False,
                "message": "Please select a resume"
            }), 400

        resume = Resume.query.filter_by(
            id=resume_id,
            candidate_id=cand.id
        ).first()

        if not resume:
            return jsonify({
                "success": False,
                "message": "Resume not found"
            }), 404

        job = Job.query.filter_by(
            id=jid,
            status="open"
        ).first()

        if not job:
            return jsonify({
                "success": False,
                "message": "Job closed"
            }), 404

        # AI Scoring
        resume_text = resume.extracted_text or ""

        job_text = f"{job.title} {job.description} {job.skills_required}"

        scores = compute_final_score(resume_text, job_text)

        match_pct = scores.get("match_percentage", 0)

        status = "shortlisted" if match_pct >= 50 else "reviewed"

        application = Application(
            job_id=jid,
            candidate_id=cand.id,
            resume_id=resume_id,
            tfidf_score=scores.get("tfidf_score", 0),
            bert_score=scores.get("bert_score", 0),
            final_score=scores.get("final_score", 0),
            match_percentage=match_pct,
            status=status,
            scored_at=datetime.utcnow(),
        )

        db.session.add(application)
        db.session.commit()

        log_action(cand.id, "APPLY_JOB", f"{job.title} Score:{match_pct}")

        return jsonify({
            "success": True,
            "scores": scores,
            "status": status
        })

    except Exception as e:

        db.session.rollback()

        print("[APPLY ERROR]")
        print(traceback.format_exc())

        return jsonify({
            "success": False,
            "message": "Application failed"
        }), 500


# -----------------------------
# My Applications + Ranking
# -----------------------------

@candidate_bp.route("/my-applications", methods=["GET"])
@jwt_required()
def my_applications():

    cand = get_candidate()

    apps = Application.query.filter_by(candidate_id=cand.id) \
        .order_by(Application.applied_at.desc()).all()

    results = []

    for app in apps:

        data = app.to_dict()

        all_apps = Application.query.filter_by(job_id=app.job_id) \
            .order_by(Application.final_score.desc()).all()

        rank = next(
            (i + 1 for i, x in enumerate(all_apps) if x.id == app.id),
            None
        )

        data["rank"] = rank
        data["total_applicants"] = len(all_apps)

        results.append(data)

    return jsonify({
        "success": True,
        "applications": results
    })


# -----------------------------
# AI Job Recommendations
# -----------------------------

@candidate_bp.route("/recommendations", methods=["GET"])
@jwt_required()
def recommend_jobs():

    cand = get_candidate()

    resume = Resume.query.filter_by(candidate_id=cand.id) \
        .order_by(Resume.uploaded_at.desc()).first()

    if not resume:
        return jsonify({"success": True, "recommendations": []})

    resume_skills = set(extract_skills(resume.extracted_text))

    jobs = Job.query.filter_by(status="open").all()

    recommendations = []

    for job in jobs:

        job_skills = set(extract_skills(job.skills_required))

        match = len(resume_skills & job_skills)

        if match > 0:
            recommendations.append({
                "job": job.to_dict(),
                "skill_match": match
            })

    recommendations.sort(
        key=lambda x: x["skill_match"], reverse=True
    )

    return jsonify({
        "success": True,
        "recommendations": recommendations[:5]
    })


# -----------------------------
# Dashboard Stats
# -----------------------------

@candidate_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():

    cand = get_candidate()

    apps = Application.query.filter_by(candidate_id=cand.id).all()

    shortlisted = sum(1 for a in apps if a.status == "shortlisted")

    avg_score = round(
        sum(a.match_percentage for a in apps) / len(apps), 1
    ) if apps else 0

    return jsonify({
        "success": True,
        "stats": {
            "total_applied": len(apps),
            "shortlisted": shortlisted,
            "avg_match": avg_score,
            "open_jobs": Job.query.filter_by(status="open").count()
        }
    })
@candidate_bp.route("/my-resumes", methods=["GET"])
@jwt_required()
def my_resumes():

    cand = get_candidate()

    resumes = Resume.query.filter_by(
        candidate_id=cand.id
    ).order_by(Resume.uploaded_at.desc()).all()

    return jsonify({
        "success": True,
        "resumes": [r.to_dict() for r in resumes]
    })