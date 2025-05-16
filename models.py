from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'parent' or 'child'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    child_profile = db.relationship('Child', backref='user', lazy=True, 
                                    primaryjoin="User.id == Child.user_id",
                                    uselist=False)
    web_activities = db.relationship('WebActivity', backref='user', lazy=True)
    emergency_logs = db.relationship('EmergencyLog', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('User', foreign_keys=[parent_id], backref='children')
    alerts = db.relationship('Alert', 
                            foreign_keys="Alert.child_id",
                            primaryjoin="Child.user_id == Alert.child_id",
                            backref='child_profile',
                            lazy=True)
    
    def __repr__(self):
        return f'<Child {self.user_id}>'

class WebActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(1024), nullable=False)
    title = db.Column(db.String(256))
    content_snippet = db.Column(db.Text)
    duration_seconds = db.Column(db.Integer)  # new field to track time
    flagged = db.Column(db.Boolean, default=False)  # new: true if inappropriate
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WebActivity {self.url}>'

class EmergencyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emergency_type = db.Column(db.String(50), nullable=False)  # e.g., "panic", "call"
    location = db.Column(db.String(255))  # optional location or GPS
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmergencyLog {self.id}>'

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alert_type = db.Column(db.String(32), nullable=False)  # 'emergency', 'inappropriate_content', etc.
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    # Relationships
    child = db.relationship('User', foreign_keys=[child_id])
    parent = db.relationship('User', foreign_keys=[parent_id])
    
    def __repr__(self):
        return f'<Alert {self.id}>'
