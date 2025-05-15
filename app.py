import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create database base class
class Base(DeclarativeBase):
    pass

# Initialize app and database
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["SQLALCHEMY_DATABASE_URI"] ="sqlite:///kidguard.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize SocketIO for real-time alerts
socketio = SocketIO(app)

# Import models after db is defined to avoid circular imports
from models import User, Child, WebActivity, Alert
from forms import LoginForm, ParentSignupForm, ChildSignupForm, EmergencyForm, ContentFilterForm

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.user_type == 'parent':
            return redirect(url_for('parent_dashboard'))
        else:
            return redirect(url_for('child_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if user.user_type == 'parent':
                return redirect(next_page or url_for('parent_dashboard'))
            else:
                return redirect(next_page or url_for('child_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/signup/parent', methods=['GET', 'POST'])
def parent_signup():
    if current_user.is_authenticated:
        return redirect(url_for('parent_dashboard'))
    
    form = ParentSignupForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        
        if existing_user:
            flash('Username already taken.', 'danger')
        elif existing_email:
            flash('Email already registered.', 'danger')
        else:
            # Create new parent user
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                user_type='parent',
                created_at=datetime.now()
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html', form=form, user_type='parent')

@app.route('/signup/child', methods=['GET', 'POST'])
def child_signup():
    if current_user.is_authenticated:
        return redirect(url_for('child_dashboard'))
    
    form = ChildSignupForm()
    # Get parent accounts for dropdown
    form.parent_id.choices = [(p.id, p.username) for p in User.query.filter_by(user_type='parent').all()]
    
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        
        if existing_user:
            flash('Username already taken.', 'danger')
        elif existing_email:
            flash('Email already registered.', 'danger')
        else:
            # Create new child user
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                user_type='child',
                created_at=datetime.now()
            )
            db.session.add(new_user)
            db.session.flush()  # Get user ID for child profile
            
            # Create child profile linked to parent
            new_child = Child(
                user_id=new_user.id,
                parent_id=form.parent_id.data,
                age=form.age.data,
                created_at=datetime.now()
            )
            db.session.add(new_child)
            db.session.commit()
            
            flash('Child account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html', form=form, user_type='child')

@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if current_user.user_type != 'parent':
        flash('Access denied. Parent account required.', 'danger')
        return redirect(url_for('home'))
    
    # Get children of this parent
    children = Child.query.filter_by(parent_id=current_user.id).all()
    child_ids = [child.user_id for child in children]
    child_users = User.query.filter(User.id.in_(child_ids)).all()
    
    # Get recent alerts
    recent_alerts = Alert.query.filter(Alert.child_id.in_(child_ids)).order_by(Alert.timestamp.desc()).limit(10).all()
    
    # Get recent web activity
    recent_activities = WebActivity.query.filter(WebActivity.user_id.in_(child_ids)).order_by(WebActivity.timestamp.desc()).limit(20).all()
    
    return render_template('parent_dashboard.html', 
                           children=child_users, 
                           alerts=recent_alerts, 
                           activities=recent_activities)

@app.route('/child/dashboard')
@login_required
def child_dashboard():
    if current_user.user_type != 'child':
        flash('Access denied. Child account required.', 'danger')
        return redirect(url_for('home'))
    
    # Get child profile
    child = Child.query.filter_by(user_id=current_user.id).first()
    if not child:
        flash('Child profile not found.', 'danger')
        return redirect(url_for('home'))
    
    # Get parent info
    parent = User.query.get(child.parent_id)
    
    # Get recent web activity
    recent_activities = WebActivity.query.filter_by(user_id=current_user.id).order_by(WebActivity.timestamp.desc()).limit(10).all()
    
    # Create emergency form
    form = EmergencyForm()
    
    return render_template('child_dashboard.html', 
                           child=child, 
                           parent=parent, 
                           activities=recent_activities,
                           form=form)

@app.route('/emergency', methods=['POST'])
@login_required
def emergency():
    if current_user.user_type != 'child':
        return jsonify({'status': 'error', 'message': 'Only children can trigger emergencies'})
    
    form = EmergencyForm()
    if form.validate_on_submit():
        child = Child.query.filter_by(user_id=current_user.id).first()
        
        # Create emergency alert
        alert = Alert(
            child_id=current_user.id,
            parent_id=child.parent_id,
            alert_type='emergency',
            message=form.message.data,
            timestamp=datetime.now()
        )
        db.session.add(alert)
        db.session.commit()
        
        # Emit real-time alert via WebSocket
        socketio.emit('new_alert', {
            'alert_id': alert.id,
            'child_name': current_user.username,
            'alert_type': 'emergency',
            'message': form.message.data,
            'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }, room=str(child.parent_id))
        
        flash('Emergency alert sent to parent.', 'success')
    else:
        flash('Failed to send emergency alert.', 'danger')
    
    return redirect(url_for('child_dashboard'))

@app.route('/report_website', methods=['POST'])
@login_required
def report_website():
    if request.method == 'POST':
        url = request.form.get('url')
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Create web activity record
        activity = WebActivity(
            user_id=current_user.id,
            url=url,
            title=title,
            content_snippet=content[:200] if content else "",  # Save first 200 chars as snippet
            timestamp=datetime.now()
        )
        db.session.add(activity)
        db.session.commit()
        
        # Check for inappropriate content
        if is_inappropriate_content(content, url):
            child = Child.query.filter_by(user_id=current_user.id).first()
            
            if child and hasattr(child,'parent_id'):
                
            # Create content alert
              alert = Alert(
                child_id=current_user.id,
                parent_id=child.parent_id,
                alert_type='inappropriate_content',
                message=f"Inappropriate content detected on: {title} ({url})",
                timestamp=datetime.now()
            )
            db.session.add(alert)
            db.session.commit()
            
            # Emit real-time alert via WebSocket
            socketio.emit('new_alert', {
                'alert_id': alert.id,
                'child_name': current_user.username,
                'alert_type': 'inappropriate_content',
                'message': f"Inappropriate content detected on: {title}",
                'url': url,
                'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }, room=str(child.parent_id))
        
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error'})

@app.route('/content_filter', methods=['GET', 'POST'])
@login_required
def content_filter():
    if current_user.user_type != 'parent':
        flash('Access denied. Parent account required.', 'danger')
        return redirect(url_for('home'))
    
    form = ContentFilterForm()
    if form.validate_on_submit():
        # Update filter settings (would normally save to database)
        flash('Content filter settings updated.', 'success')
    
    return render_template('content_filter.html', form=form)

@app.route('/alert/<int:alert_id>')
@login_required
def view_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    
    # Ensure parent can only view their children's alerts
    if current_user.user_type == 'parent' and alert.parent_id != current_user.id:
        flash('Access denied. Not your alert.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    # Ensure children can only view their own alerts
    if current_user.user_type == 'child' and alert.child_id != current_user.id:
        flash('Access denied. Not your alert.', 'danger')
        return redirect(url_for('child_dashboard'))
    
    child = User.query.get(alert.child_id)
    
    return render_template('alert.html', alert=alert, child=child)

@app.route('/child/<int:child_id>/settings', methods=['GET', 'POST'])
@login_required
def child_settings(child_id):
    if current_user.user_type != 'parent':
        flash('Access denied. Parent account required.', 'danger')
        return redirect(url_for('home'))
    
    # Get the child profile
    child = Child.query.get_or_404(child_id)
    
    # Ensure parent can only access their own children's settings
    if child.parent_id != current_user.id:
        flash('Access denied. Not your child.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    # Handle form submission (in a real app, you'd save the settings)
    if request.method == 'POST':
        # This would save the settings to the database in a real implementation
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('parent_dashboard'))
    
    return render_template('child_settings.html', child=child)

@app.route('/clear_activity_data')
@login_required
def clear_activity_data():
    if current_user.user_type == 'parent':
        # For a parent, clear all their children's activities
        children = Child.query.filter_by(parent_id=current_user.id).all()
        child_ids = [child.user_id for child in children]
        
        WebActivity.query.filter(WebActivity.user_id.in_(child_ids)).delete(synchronize_session=False)
        Alert.query.filter(Alert.child_id.in_(child_ids)).delete(synchronize_session=False)
        
    else:
        # For a child, clear only their activities
        WebActivity.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
        Alert.query.filter_by(child_id=current_user.id).delete(synchronize_session=False)
    
    db.session.commit()
    flash('Activity history has been cleared.', 'success')
    
    if current_user.user_type == 'parent':
        return redirect(url_for('parent_dashboard'))
    else:
        return redirect(url_for('child_dashboard'))

@app.route('/check_users')
def check_users():
    users = User.query.all()
    if users:
        return '<br>'.join([f'{u.username} ({u.user_type})' for u in users])
    else:
        return 'No users found in database.'

    
# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        # Join a room based on user ID for targeted notifications
        socketio.emit('join', {'room': str(current_user.id)})

def is_inappropriate_content(content, url):
    """Check if content is inappropriate based on keywords and domain blocklists."""
    if not content or not url:
        return False
    
    # List of inappropriate keywords (this would be more sophisticated in production)
    inappropriate_keywords = [
        'porn', 'sex', 'nude', 'gambling', 'violence', 'drugs', 'alcohol',
        'weapon', 'betting', 'adult', 'xxx', 'explicit'
    ]
    
    # Check for inappropriate domains (this would be more sophisticated in production)
    blocked_domains = [
        'adult', 'porn', 'xxx', 'betting', 'gambling', 'sex'
    ]
    
    # Check content for inappropriate keywords
    content_lower = content.lower()
    for keyword in inappropriate_keywords:
        if keyword in content_lower:
            return True
    
    # Check URL for blocked domains
    url_lower = url.lower()
    for domain in blocked_domains:
        if domain in url_lower:
            return True
    
    return False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
