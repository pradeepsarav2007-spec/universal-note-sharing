from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationships
    notes = db.relationship('Note', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')
    downloads = db.relationship('DownloadHistory', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def total_notes_uploaded(self):
        return self.notes.filter_by(is_approved=True).count()
    
    @property
    def total_downloads_received(self):
        total = 0
        for note in self.notes.all():
            total += note.download_count
        return total
    
    @property
    def initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return "U"
        
    def __repr__(self):
        return f'<User {self.email}>'


class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    icon = db.Column(db.String(50), default='fa-graduation-cap')
    description = db.Column(db.Text, nullable=True)
    
    # Relationship
    notes = db.relationship('Note', backref='department_rel', lazy='dynamic')
    
    @property
    def note_count(self):
        return self.notes.filter_by(is_approved=True).count()
        
    def __repr__(self):
        return f'<Department {self.name}>'


class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    subject = db.Column(db.String(150), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.Column(db.String(100), nullable=False)  # stored textual name for quick lookup & backward compatibility
    semester = db.Column(db.Integer, nullable=False, default=1)  # 1 - 8
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255), nullable=True)  # comma separated
    
    # File details
    filename = db.Column(db.String(255), nullable=False)  # Stored unique filename
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'pdf', 'docx', 'pptx', etc.
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    
    # Metadata
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    downloads = db.relationship('DownloadHistory', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def formatted_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} GB"
    
    @property
    def file_icon(self):
        ext = self.file_type.lower()
        if ext == 'pdf':
            return 'fa-file-pdf text-red-500'
        elif ext in ['docx', 'doc']:
            return 'fa-file-word text-blue-500'
        elif ext in ['pptx', 'ppt']:
            return 'fa-file-powerpoint text-orange-500'
        elif ext == 'txt':
            return 'fa-file-lines text-slate-500'
        return 'fa-file text-indigo-500'
        
    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def __repr__(self):
        return f'<Note {self.title}>'


class DownloadHistory(db.Model):
    __tablename__ = 'download_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # nullable for guests
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    downloaded_at = db.Column(db.DateTime, default=utc_now)
    
    def __repr__(self):
        return f'<Download Note={self.note_id} User={self.user_id}>'
