from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    return render_template('login.html')

@pages_bp.route('/login')
def login():
    return render_template('login.html')

@pages_bp.route('/register')
def register():
    return render_template('register.html')

@pages_bp.route('/verify-otp')
def verify_otp():
    return render_template('verify_otp.html')

@pages_bp.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@pages_bp.route('/admin')
def admin():
    return render_template('admin.html')

@pages_bp.route('/recruiter')
def recruiter():
    return render_template('recruiter.html')

@pages_bp.route('/candidate')
def candidate():
    return render_template('candidate.html')

@pages_bp.route('/ml-dashboard')
def ml_dashboard():
    return render_template('ml_dashboard.html')
