from app import db
from datetime import datetime

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.Text, nullable=False)
    experience_required = db.Column(db.String(50))
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(50), default='Full-time')
    status = db.Column(db.String(20), default='open')  # open, closed
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='job', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'skills_required': self.skills_required,
            'experience_required': self.experience_required,
            'location': self.location,
            'job_type': self.job_type,
            'status': self.status,
            'recruiter_id': self.recruiter_id,
            'recruiter_name': self.recruiter.name if self.recruiter else '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'application_count': len(self.applications)
        }


class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    extracted_text = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='resume', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M')
        }


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    tfidf_score = db.Column(db.Float, default=0.0)
    bert_score = db.Column(db.Float, default=0.0)
    final_score = db.Column(db.Float, default=0.0)
    match_percentage = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='pending')  # pending, shortlisted, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    scored_at = db.Column(db.DateTime, nullable=True)

    candidate = db.relationship('User', foreign_keys=[candidate_id])

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_title': self.job.title if self.job else '',
            'candidate_id': self.candidate_id,
            'candidate_name': self.candidate.name if self.candidate else '',
            'candidate_email': self.candidate.email if self.candidate else '',
            'resume_id': self.resume_id,
            'resume_filename': self.resume.filename if self.resume else '',
            'tfidf_score': round(self.tfidf_score, 4),
            'bert_score': round(self.bert_score, 4),
            'final_score': round(self.final_score, 4),
            'match_percentage': round(self.match_percentage, 2),
            'status': self.status,
            'applied_at': self.applied_at.strftime('%Y-%m-%d %H:%M'),
            'scored_at': self.scored_at.strftime('%Y-%m-%d %H:%M') if self.scored_at else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.email if self.user else 'System',
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
