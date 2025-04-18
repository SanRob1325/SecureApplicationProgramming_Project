from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

# Reference to model migrations and SQL conversion of models https://medium.com/@shivamkhandelwal555/a-proper-way-of-declaring-models-in-flask-9ce0bb0e42c1
# User table
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(128), nullable=False)
    encryption_key = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    credentials = db.relationship('Credential', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    logs = db.relationship('Log', backref='user', lazy='dynamic')

    auth_token = db.Column(db.String(64),nullable=True)
    auth_token_expiry = db.Column(db.DateTime, nullable=True)
    def __repr__(self):
        return '<User {self.username}>'

    def get_auth_token(self):
        """Generate a secure token for remember me functionality"""
        import secrets
        from datetime import datetime,timedelta

        # Generate token if it doesn't exist or has expired
        if not self.auth_token or \
            self.auth_token_expiry or \
            self.auth_token_expiry < datetime.utcnow():

            self.auth_token = secrets.token_hex(32)
            self.auth_token_expiry = datetime.utcnow() + timedelta(days=30)
            db.session.add(self)
        return self.auth_token

# Credential table
class Credential(db.Model):
    __tablename__ = 'credentials'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_name = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(128), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=True)
    iv = db.Column(db.String(128), nullable=False) # initialisation vector for encryption
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Credential {self.service_name} for {self.user.username}>'

# Log table
class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Log {self.event_type} at {self.user_id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
