import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()


def create_app():
    """Application Factory"""

    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )

    configure_app(app)
    initialize_extensions(app)
    register_blueprints(app)
    setup_database(app)

    return app


# -----------------------------
# Configuration
# -----------------------------
def configure_app(app):

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    app.config.update(

        SECRET_KEY=os.getenv("SECRET_KEY", "smart_recruitment_secret"),

        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(BASE_DIR, "recruitment.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "jwt_secret_key"),
        JWT_TOKEN_LOCATION=["headers", "cookies"],
        JWT_COOKIE_SECURE=False,
        JWT_ACCESS_TOKEN_EXPIRES=False,

        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME"),

        UPLOAD_FOLDER=os.path.join(BASE_DIR, "uploads")
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# -----------------------------
# Extensions
# -----------------------------
def initialize_extensions(app):

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)


# -----------------------------
# Blueprints
# -----------------------------
def register_blueprints(app):

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.recruiter import recruiter_bp
    from routes.candidate import candidate_bp
    from routes.ml_routes import ml_bp
    from routes.pages import pages_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(recruiter_bp, url_prefix="/api/recruiter")
    app.register_blueprint(candidate_bp, url_prefix="/api/candidate")
    app.register_blueprint(ml_bp, url_prefix="/api/ml")

    app.register_blueprint(pages_bp)


# -----------------------------
# Database Setup
# -----------------------------
def setup_database(app):

    with app.app_context():

        db.create_all()

        seed_admin()
        seed_sample_jobs()


# -----------------------------
# Seed Admin
# -----------------------------
def seed_admin():

    from models.user import User
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(email="admin@recruitment.com").first()

    if not admin:

        admin = User(
            name="System Admin",
            email="admin@recruitment.com",
            password=generate_password_hash("Admin@123"),
            role="admin",
            is_verified=True,
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin created → admin@recruitment.com / Admin@123")


# -----------------------------
# Seed Sample Jobs
# -----------------------------
def seed_sample_jobs():

    from models.user import User
    from models.models import Job
    from werkzeug.security import generate_password_hash

    if Job.query.count() > 0:
        return

    recruiter = User.query.filter_by(email="recruiter@demo.com").first()

    if not recruiter:

        recruiter = User(
            name="Demo Recruiter",
            email="recruiter@demo.com",
            password=generate_password_hash("Demo@123"),
            role="recruiter",
            is_verified=True,
            is_active=True
        )

        db.session.add(recruiter)
        db.session.flush()

    jobs = [
        {
            "title": "Python Backend Developer",
            "description": "Build scalable backend APIs using Python.",
            "skills_required": "Python, Flask, FastAPI, SQL, Docker",
            "experience_required": "2-4 years",
            "location": "Bangalore",
            "job_type": "Full-time"
        },
        {
            "title": "Machine Learning Engineer",
            "description": "Develop ML models and deploy AI systems.",
            "skills_required": "Python, TensorFlow, PyTorch, NLP, BERT",
            "experience_required": "3-5 years",
            "location": "Hyderabad",
            "job_type": "Full-time"
        }
    ]

    for j in jobs:

        job = Job(
            recruiter_id=recruiter.id,
            status="open",
            **j
        )

        db.session.add(job)

    db.session.commit()

    print("Sample jobs inserted")


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":

    app = create_app()

    app.run(debug=True, port=5000)