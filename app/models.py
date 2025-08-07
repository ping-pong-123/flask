# app/models.py
from . import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    # 🔹 The relationship to the Scan model is defined here.
    #    'back_populates' creates a two-way link.
    scans = db.relationship('Scan', back_populates='user', lazy=True) 


class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_name = db.Column(db.String(150), nullable=False)
    target_url = db.Column(db.String(2083), nullable=False)
    scan_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="In Progress")
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.Text)

    # Timestamps
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    # Auth & cookies
    auth_type = db.Column(db.String(20), default="none")
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    token = db.Column(db.String(200))
    cookies = db.Column(db.Text)

    # 🔹 New fields
    environment = db.Column(db.String(50), nullable=False, default="dev")  # dev/staging/production
    tags = db.Column(db.String(255))  # Comma-separated tags like "Web App, Internal"
    vulnerabilities = db.relationship("Vulnerability", backref="scan", lazy=True)

    # New column to store the full scan log
    log_data = db.Column(db.Text)
    # 🔹 This 'relationship' and 'back_populates' are what create the 'scan.user' attribute
    user = db.relationship('User', back_populates='scans')
    # 🔹 NEW: Add a column to track if the scan is paused
    is_paused = db.Column(db.Boolean, default=False)

class Vulnerability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scan.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(50), nullable=False)  # e.g., Critical, High, Medium, Low, Info
    description = db.Column(db.Text)
    affected_url = db.Column(db.String(2083))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CommandExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scan.id'), nullable=False)
    command_text = db.Column(db.String(1024), nullable=False)
    decision = db.Column(db.String(20), nullable=True)  # approve / skip / terminate
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    wait_started_at = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)

    # Optional: Link back to Scan
    scan = db.relationship('Scan', backref='command_executions')