from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.models import Application
import os, json

ml_bp = Blueprint('ml', __name__)

def require_admin_or_recruiter():
    uid = get_jwt_identity()
    user = User.query.get(int(uid))
    return user if user and user.role in ['admin', 'recruiter'] else None


@ml_bp.route('/status', methods=['GET'])
@jwt_required()
def model_status():
    user = require_admin_or_recruiter()
    if not user: return jsonify({'success': False}), 403

    bert_available = False
    tfidf_available = False
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        tfidf_available = True
    except: pass
    try:
        from sentence_transformers import SentenceTransformer
        bert_available = True
    except: pass

    return jsonify({
        'success': True,
        'models': {
            'tfidf': {'available': tfidf_available, 'library': 'scikit-learn'},
            'bert': {'available': bert_available, 'model': 'all-MiniLM-L6-v2', 'library': 'sentence-transformers'},
        },
        'scoring_formula': 'Final Score = (TF-IDF × 0.4) + (BERT × 0.6)',
        'shortlist_threshold': '50%'
    })


@ml_bp.route('/test-score', methods=['POST'])
@jwt_required()
def test_score():
    """Test the scoring engine with custom text input."""
    user = require_admin_or_recruiter()
    if not user: return jsonify({'success': False}), 403

    data = request.get_json()
    resume_text = data.get('resume_text', '')
    job_text = data.get('job_text', '')

    if not resume_text or not job_text:
        return jsonify({'success': False, 'message': 'Both resume_text and job_text required'}), 400

    from ml.scorer import compute_final_score, extract_skills
    scores = compute_final_score(resume_text, job_text)
    skills = extract_skills(resume_text)

    return jsonify({
        'success': True,
        'scores': scores,
        'extracted_skills': skills,
        'shortlisted': scores['match_percentage'] >= 50
    })


@ml_bp.route('/analytics', methods=['GET'])
@jwt_required()
def analytics():
    """Score distribution and model performance stats."""
    user = require_admin_or_recruiter()
    if not user: return jsonify({'success': False}), 403

    apps = Application.query.all()
    if not apps:
        return jsonify({'success': True, 'analytics': {}, 'message': 'No data yet'})

    scores = [a.match_percentage for a in apps]
    shortlisted = [a for a in apps if a.status == 'shortlisted']
    rejected = [a for a in apps if a.status == 'rejected']

    buckets = {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
    for s in scores:
        if s <= 20: buckets['0-20'] += 1
        elif s <= 40: buckets['21-40'] += 1
        elif s <= 60: buckets['41-60'] += 1
        elif s <= 80: buckets['61-80'] += 1
        else: buckets['81-100'] += 1

    return jsonify({
        'success': True,
        'analytics': {
            'total_scored': len(apps),
            'shortlisted': len(shortlisted),
            'rejected': len(rejected),
            'avg_score': round(sum(scores)/len(scores), 2),
            'max_score': round(max(scores), 2),
            'min_score': round(min(scores), 2),
            'score_distribution': buckets
        }
    })


@ml_bp.route('/install-check', methods=['GET'])
@jwt_required()
def install_check():
    results = {}
    libs = ['sklearn', 'sentence_transformers', 'pdfplumber', 'PyPDF2', 'numpy', 'flask_mail']
    for lib in libs:
        try:
            __import__(lib)
            results[lib] = '✅ Installed'
        except ImportError:
            results[lib] = '❌ Not installed'
    return jsonify({'success': True, 'libraries': results})
