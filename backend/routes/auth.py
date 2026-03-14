from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app import db, mail
from models.user import User
from models.models import AuditLog
from datetime import datetime, timedelta
import random, string

auth_bp = Blueprint('auth', __name__)

def log_action(user_id, action, details='', ip=''):
    log = AuditLog(user_id=user_id, action=action, details=details, ip_address=ip)
    db.session.add(log)
    db.session.commit()

def send_otp_email(email, otp, name):
    try:
        msg = Message(
            subject='Your OTP - Smart Recruitment System',
            recipients=[email],
            html=f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:10px;">
              <h2 style="color:#4f46e5;">Smart Recruitment System</h2>
              <p>Hello <b>{name}</b>,</p>
              <p>Your One-Time Password for verification is:</p>
              <div style="font-size:36px;font-weight:bold;letter-spacing:10px;color:#4f46e5;padding:16px;background:#f3f4f6;border-radius:8px;text-align:center;">{otp}</div>
              <p>This OTP is valid for <b>10 minutes</b>.</p>
              <p style="color:#6b7280;font-size:12px;">If you did not request this, please ignore this email.</p>
            </div>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[Mail Error] {e}")
        return False


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'candidate')

    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    if role not in ['candidate', 'recruiter']:
        role = 'candidate'
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409

    otp = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.utcnow() + timedelta(minutes=10)

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role,
        otp=otp,
        otp_expiry=expiry,
        is_verified=False
    )
    db.session.add(user)
    db.session.commit()

    sent = send_otp_email(email, otp, name)
    log_action(user.id, 'REGISTER', f'New {role} registered', request.remote_addr)

    return jsonify({
        'success': True,
        'message': 'Registration successful. OTP sent to your email.' if sent else 'Registration successful. Email not sent (check mail config). OTP: ' + otp,
        'user_id': user.id,
        'dev_otp': otp  # remove in production
    })


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email', '').lower()
    otp = data.get('otp', '')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    if user.is_verified:
        return jsonify({'success': True, 'message': 'Already verified'})
    if user.otp != otp:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400
    if datetime.utcnow() > user.otp_expiry:
        return jsonify({'success': False, 'message': 'OTP expired. Please register again'}), 400

    user.is_verified = True
    user.otp = None
    user.otp_expiry = None
    db.session.commit()
    log_action(user.id, 'VERIFY_OTP', 'Email verified', request.remote_addr)

    token = create_access_token(identity=str(user.id))
    return jsonify({'success': True, 'message': 'Email verified!', 'token': token, 'role': user.role, 'name': user.name})


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    if not user.is_verified:
        return jsonify({'success': False, 'message': 'Please verify your email first', 'need_verify': True, 'email': email}), 403
    if not user.is_active:
        return jsonify({'success': False, 'message': 'Account disabled. Contact admin'}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()
    log_action(user.id, 'LOGIN', 'User logged in', request.remote_addr)

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'success': True,
        'token': token,
        'role': user.role,
        'name': user.name,
        'email': user.email,
        'user_id': user.id
    })


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'Email not found'}), 404

    otp = ''.join(random.choices(string.digits, k=6))
    user.otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    send_otp_email(email, otp, user.name)
    return jsonify({'success': True, 'message': 'OTP sent to your email', 'dev_otp': otp})


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email', '').lower()
    otp = data.get('otp', '')
    new_password = data.get('new_password', '')

    user = User.query.filter_by(email=email).first()
    if not user or user.otp != otp:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400
    if datetime.utcnow() > user.otp_expiry:
        return jsonify({'success': False, 'message': 'OTP expired'}), 400

    user.password = generate_password_hash(new_password)
    user.otp = None
    user.otp_expiry = None
    db.session.commit()
    log_action(user.id, 'PASSWORD_RESET', 'Password reset', request.remote_addr)
    return jsonify({'success': True, 'message': 'Password reset successful'})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = User.query.get(int(uid))
    if not user:
        return jsonify({'success': False}), 404
    return jsonify({'success': True, 'user': user.to_dict()})
