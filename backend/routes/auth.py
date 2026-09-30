from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from backend.database import get_db
from backend.db_models import User

auth_bp = Blueprint('auth', __name__)

def role_required(*allowed_roles):
    """Decorator to enforce role-based access control on routes."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in allowed_roles:
                flash("Access denied: You do not have permission to view this resource.", "danger")
                if current_user.role == 'farmer':
                    return redirect(url_for('farmer.dashboard'))
                elif current_user.role == 'vet':
                    return redirect(url_for('vet.dashboard'))
                elif current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'farmer':
            return redirect(url_for('farmer.dashboard'))
        elif current_user.role == 'vet':
            return redirect(url_for('vet.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not login_id or not password:
            flash("Please enter both username/email and password.", "warning")
            return render_template('auth/login.html')

        db = get_db()
        user = db.query(User).filter(
            (User.username == login_id) | (User.email == login_id)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been deactivated. Please contact your administrator.", "danger")
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name}!", "success")

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            if user.role == 'farmer':
                return redirect(url_for('farmer.dashboard'))
            elif user.role == 'vet':
                return redirect(url_for('vet.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials. Please verify your login details.", "danger")

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Self-registration for Farmers."""
    if current_user.is_authenticated:
        return redirect(url_for('farmer.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()

        # Validation
        if not username or not email or not full_name or not password:
            flash("All mandatory fields must be completed.", "warning")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return render_template('auth/register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return render_template('auth/register.html')

        db = get_db()
        existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash("A user with this username or email already exists.", "danger")
            return render_template('auth/register.html')

        new_farmer = User(
            username=username,
            email=email,
            full_name=full_name,
            role='farmer',
            phone=phone,
            location=location
        )
        new_farmer.set_password(password)
        db.add(new_farmer)
        db.commit()

        login_user(new_farmer)
        flash("Farmer registration successful! Welcome to GoShala Care.", "success")
        return redirect(url_for('farmer.dashboard'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('auth.login'))
