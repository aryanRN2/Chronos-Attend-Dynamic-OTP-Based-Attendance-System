
import random
import string
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

from models import db, User, AttendanceSession, AttendanceRecord

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables within application context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login failed. Please check email and password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access restricted to teachers.', 'danger')
        return redirect(url_for('index'))
        
    # Get the latest active session for this teacher
    now = datetime.now(timezone.utc)
    active_session = AttendanceSession.query.filter(
        AttendanceSession.teacher_id == current_user.id,
        AttendanceSession.is_active == True,
        AttendanceSession.expires_at > now
    ).order_by(AttendanceSession.created_at.desc()).first()
    
    # Check if there are any sessions that should be deactivated
    expired_sessions = AttendanceSession.query.filter(
        AttendanceSession.teacher_id == current_user.id,
        AttendanceSession.is_active == True,
        AttendanceSession.expires_at <= now
    ).all()
    for session in expired_sessions:
        session.is_active = False
    if expired_sessions:
        db.session.commit()

    records = []
    if active_session:
        records = AttendanceRecord.query.filter_by(session_id=active_session.id).order_by(AttendanceRecord.timestamp.desc()).all()
        
    return render_template('teacher_dashboard.html', active_session=active_session, records=records, now=now)

@app.route('/generate_session', methods=['POST'])
@login_required
def generate_session():
    if current_user.role != 'teacher':
        flash('Only teachers can generate sessions.', 'danger')
        return redirect(url_for('index'))
        
    # Deactivate existing active sessions
    active_sessions = AttendanceSession.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    for session in active_sessions:
        session.is_active = False
        
    otp = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    new_session = AttendanceSession(teacher_id=current_user.id, otp=otp, expires_at=expires_at)
    db.session.add(new_session)
    db.session.commit()
    
    flash('New attendance session generated successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/student_dashboard', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access restricted to students.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        otp_attempt = request.form.get('otp')
        now = datetime.now(timezone.utc)
        
        # Find if the OTP matches any active session that hasn't expired
        valid_session = AttendanceSession.query.filter(
            AttendanceSession.otp == otp_attempt,
            AttendanceSession.is_active == True,
            AttendanceSession.expires_at > now
        ).first()
        
        if valid_session:
            # Check if student already marked attendance for this session
            existing_record = AttendanceRecord.query.filter_by(
                student_id=current_user.id, 
                session_id=valid_session.id
            ).first()
            
            if existing_record:
                flash('You have already marked your attendance for this session.', 'info')
            else:
                new_record = AttendanceRecord(student_id=current_user.id, session_id=valid_session.id)
                db.session.add(new_record)
                db.session.commit()
                flash('Attendance marked successfully!', 'success')
        else:
            flash('Invalid or expired OTP.', 'danger')
            
        return redirect(url_for('student_dashboard'))
        
    # Display recent attendance history for the student
    history = AttendanceRecord.query.filter_by(student_id=current_user.id).order_by(AttendanceRecord.timestamp.desc()).limit(10).all()
    return render_template('student_dashboard.html', history=history)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
