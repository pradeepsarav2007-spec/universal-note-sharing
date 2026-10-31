import os
import uuid
from functools import wraps
from pathlib import Path
from datetime import datetime, timezone

from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, abort, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Department, Note, DownloadHistory

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory and instance directory exist
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
(Config.BASE_DIR / 'instance').mkdir(parents=True, exist_ok=True)

db.init_app(app)

# Ensure database tables and initial categories exist
with app.app_context():
    db.create_all()
    try:
        if Department.query.count() == 0:
            from seed_data import seed_database
            seed_database()
    except Exception as e:
        print(f"Auto-init check notice: {e}")

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Authentication helper decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in or create an account to access this feature.', 'info')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin access requires logging in first.', 'warning')
            return redirect(url_for('login', next=request.url))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to make current_user and departments available to all templates
@app.context_processor
def inject_global_data():
    current_user = None
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])
        if not current_user or not current_user.is_active:
            # If user was deleted or banned while logged in
            session.clear()
            current_user = None
            
    departments = Department.query.order_by(Department.name).all()
    total_notes_count = Note.query.filter_by(is_approved=True).count()
    
    return {
        'current_user': current_user,
        'global_departments': departments,
        'global_total_notes': total_notes_count,
        'current_year': datetime.now(timezone.utc).year
    }

# ----------------- HOME PAGE -----------------
@app.route('/')
def index():
    # Hero stats
    total_notes = Note.query.filter_by(is_approved=True).count()
    total_users = User.query.filter_by(is_active=True).count()
    
    # Calculate total downloads
    total_downloads = db.session.query(db.func.sum(Note.download_count)).scalar() or 0
    total_departments = Department.query.count()
    
    # Recent notes (latest 6)
    recent_notes = Note.query.filter_by(is_approved=True)\
        .order_by(Note.created_at.desc()).limit(6).all()
        
    # Popular notes (top 6 by downloads)
    popular_notes = Note.query.filter_by(is_approved=True)\
        .order_by(Note.download_count.desc(), Note.view_count.desc()).limit(6).all()
        
    # Featured notes if any
    featured_notes = Note.query.filter_by(is_approved=True, is_featured=True)\
        .order_by(Note.created_at.desc()).limit(4).all()
        
    # Department categories
    departments = Department.query.order_by(Department.name).all()
    
    return render_template('index.html',
                           recent_notes=recent_notes,
                           popular_notes=popular_notes,
                           featured_notes=featured_notes,
                           departments=departments,
                           stats={
                               'notes': total_notes,
                               'users': total_users,
                               'downloads': total_downloads,
                               'departments': total_departments
                           })

# ----------------- NOTES LIBRARY PAGE -----------------
@app.route('/library')
def library():
    # Filters from query params
    search_query = request.args.get('q', '').strip()
    selected_dept = request.args.get('department', '').strip()
    selected_semester = request.args.get('semester', '').strip()
    selected_format = request.args.get('format', '').strip()
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Query builder
    query = Note.query.filter_by(is_approved=True)

    # Search filter
    if search_query:
        search_filter = (
            Note.title.ilike(f'%{search_query}%') |
            Note.subject.ilike(f'%{search_query}%') |
            Note.description.ilike(f'%{search_query}%') |
            Note.tags.ilike(f'%{search_query}%')
        )
        query = query.filter(search_filter)

    # Department filter
    if selected_dept and selected_dept != 'all':
        query = query.filter(Note.department == selected_dept)

    # Semester filter
    if selected_semester and selected_semester != 'all':
        try:
            sem_int = int(selected_semester)
            query = query.filter(Note.semester == sem_int)
        except ValueError:
            pass

    # File Format filter
    if selected_format and selected_format != 'all':
        if selected_format == 'doc':
            query = query.filter(Note.file_type.in_(['doc', 'docx']))
        elif selected_format == 'ppt':
            query = query.filter(Note.file_type.in_(['ppt', 'pptx']))
        else:
            query = query.filter(Note.file_type == selected_format)

    # Sorting
    if sort_by == 'popular':
        query = query.order_by(Note.download_count.desc(), Note.view_count.desc())
    elif sort_by == 'views':
        query = query.order_by(Note.view_count.desc())
    elif sort_by == 'title':
        query = query.order_by(Note.title.asc())
    elif sort_by == 'oldest':
        query = query.order_by(Note.created_at.asc())
    else:  # newest
        query = query.order_by(Note.created_at.desc())

    # Pagination
    paginated_notes = query.paginate(page=page, per_page=per_page, error_out=False)
    
    departments = Department.query.order_by(Department.name).all()

    return render_template('library.html',
                           notes=paginated_notes.items,
                           pagination=paginated_notes,
                           search_query=search_query,
                           selected_dept=selected_dept,
                           selected_semester=selected_semester,
                           selected_format=selected_format,
                           sort_by=sort_by,
                           departments=departments,
                           total_results=paginated_notes.total)

# ----------------- NOTES DETAILS PAGE -----------------
@app.route('/notes/<int:note_id>')
def note_detail(note_id):
    note = db.get_or_404(Note, note_id)
    
    # Increment view count
    note.view_count += 1
    db.session.commit()
    
    # Fetch related notes in the same subject or department
    related_notes = Note.query.filter(
        Note.id != note.id,
        Note.is_approved == True,
        (Note.subject == note.subject) | (Note.department == note.department)
    ).order_by(Note.download_count.desc()).limit(4).all()
    
    return render_template('note_detail.html', note=note, related_notes=related_notes)

# ----------------- DOWNLOAD NOTE -----------------
@app.route('/notes/<int:note_id>/download')
def download_note(note_id):
    note = db.get_or_404(Note, note_id)
    
    file_path = Config.UPLOAD_FOLDER / note.filename
    if not file_path.exists():
        flash('Sorry, the requested file is missing from the server storage.', 'danger')
        return redirect(url_for('note_detail', note_id=note.id))
        
    # Increment download count
    note.download_count += 1
    
    # Log download history
    download_record = DownloadHistory(
        user_id=session.get('user_id'),
        note_id=note.id,
        ip_address=request.remote_addr
    )
    db.session.add(download_record)
    db.session.commit()
    
    return send_from_directory(
        directory=str(Config.UPLOAD_FOLDER),
        path=note.filename,
        as_attachment=True,
        download_name=note.original_filename
    )

# ----------------- PREVIEW / INLINE VIEW FILE -----------------
@app.route('/notes/<int:note_id>/preview')
def preview_note(note_id):
    note = db.get_or_404(Note, note_id)
    file_path = Config.UPLOAD_FOLDER / note.filename
    
    if not file_path.exists():
        abort(404, description="File not found on server")
        
    # Map mime type
    mime_types = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'ppt': 'application/vnd.ms-powerpoint'
    }
    mimetype = mime_types.get(note.file_type.lower(), 'application/octet-stream')
    
    return send_from_directory(
        directory=str(Config.UPLOAD_FOLDER),
        path=note.filename,
        as_attachment=False,
        mimetype=mimetype
    )

# ----------------- UPLOAD NOTES PAGE -----------------
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    departments = Department.query.order_by(Department.name).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject = request.form.get('subject', '').strip()
        department = request.form.get('department', '').strip()
        semester_str = request.form.get('semester', '1').strip()
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        
        # Validations
        if not title or not subject or not department or not description:
            flash('All required fields (Title, Subject, Department, Description) must be filled.', 'danger')
            return render_template('upload.html', departments=departments)
            
        try:
            semester = int(semester_str)
            if semester < 1 or semester > 8:
                semester = 1
        except ValueError:
            semester = 1

        # Check file
        if 'file' not in request.files:
            flash('Please select a file to upload.', 'danger')
            return render_template('upload.html', departments=departments)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file was selected.', 'danger')
            return render_template('upload.html', departments=departments)
            
        if not allowed_file(file.filename):
            flash('Invalid file format. Allowed formats: PDF, DOCX, DOC, PPTX, PPT, TXT.', 'danger')
            return render_template('upload.html', departments=departments)
            
        # Secure filename and unique storage name
        original_name = secure_filename(file.filename)
        file_ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else 'dat'
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        destination = Config.UPLOAD_FOLDER / unique_name
        
        # Save file to disk
        file.save(str(destination))
        file_size = destination.stat().st_size
        
        # Match department ID if exists
        dept_obj = Department.query.filter_by(name=department).first()
        dept_id = dept_obj.id if dept_obj else None

        # Create note record
        new_note = Note(
            title=title,
            subject=subject,
            department=department,
            department_id=dept_id,
            semester=semester,
            description=description,
            tags=tags,
            filename=unique_name,
            original_filename=original_name,
            file_type=file_ext,
            file_size=file_size,
            user_id=session['user_id']
        )
        
        db.session.add(new_note)
        db.session.commit()
        
        flash(f'Success! "{title}" has been uploaded and published to the Universal Library.', 'success')
        return redirect(url_for('note_detail', note_id=new_note.id))

    return render_template('upload.html', departments=departments)

# ----------------- EDIT NOTE -----------------
@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = db.get_or_404(Note, note_id)
    current_user_id = session.get('user_id')
    user = db.session.get(User, current_user_id)
    
    # Permission check: must be owner or admin
    if note.user_id != current_user_id and not (user and user.is_admin):
        flash('You are not authorized to edit this note.', 'danger')
        return redirect(url_for('note_detail', note_id=note.id))
        
    departments = Department.query.order_by(Department.name).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject = request.form.get('subject', '').strip()
        department = request.form.get('department', '').strip()
        semester_str = request.form.get('semester', '1').strip()
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        
        if not title or not subject or not department or not description:
            flash('Please complete all required fields.', 'danger')
            return render_template('edit_note.html', note=note, departments=departments)
            
        note.title = title
        note.subject = subject
        note.department = department
        try:
            note.semester = int(semester_str)
        except ValueError:
            pass
        note.description = description
        note.tags = tags
        
        # Optional replacement file
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if allowed_file(file.filename):
                # Remove old file
                old_file = Config.UPLOAD_FOLDER / note.filename
                if old_file.exists():
                    try:
                        old_file.unlink()
                    except OSError:
                        pass
                
                original_name = secure_filename(file.filename)
                file_ext = original_name.rsplit('.', 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                destination = Config.UPLOAD_FOLDER / unique_name
                file.save(str(destination))
                
                note.filename = unique_name
                note.original_filename = original_name
                note.file_type = file_ext
                note.file_size = destination.stat().st_size
                
        note.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        flash('Note has been successfully updated.', 'success')
        return redirect(url_for('note_detail', note_id=note.id))

    return render_template('edit_note.html', note=note, departments=departments)

# ----------------- DELETE NOTE -----------------
@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = db.get_or_404(Note, note_id)
    current_user_id = session.get('user_id')
    user = db.session.get(User, current_user_id)
    
    # Permission check: must be owner or admin
    if note.user_id != current_user_id and not (user and user.is_admin):
        flash('Unauthorized operation.', 'danger')
        return redirect(url_for('note_detail', note_id=note.id))
        
    # Delete file from disk
    file_path = Config.UPLOAD_FOLDER / note.filename
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass
            
    note_title = note.title
    db.session.delete(note)
    db.session.commit()
    
    flash(f'Note "{note_title}" has been deleted successfully.', 'info')
    
    # Redirect back to where user came from
    referrer = request.referrer or ''
    if 'admin' in referrer:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('user_dashboard'))

# ----------------- AUTHENTICATION: REGISTER -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validations
        if not full_name or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('login'))
            
        # Create user
        new_user = User(
            full_name=full_name,
            email=email,
            department=department,
            role='user'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Automatically log in the user
        session['user_id'] = new_user.id
        session['user_name'] = new_user.full_name
        session['user_email'] = new_user.email
        session['user_role'] = new_user.role
        
        flash(f'Welcome to Universal Notes, {new_user.full_name}! Your account has been created.', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('register.html')

# ----------------- AUTHENTICATION: LOGIN -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
        
    next_url = request.args.get('next')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html', next=next_url)
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', next=next_url)
            
        if not user.is_active:
            flash('This account has been deactivated. Please contact support.', 'danger')
            return render_template('login.html', next=next_url)
            
        # Store in session
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['user_email'] = user.email
        session['user_role'] = user.role
        
        flash(f'Welcome back, {user.full_name}!', 'success')
        
        # Check next redirect url
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
            
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))

    return render_template('login.html', next=next_url)

# ----------------- AUTHENTICATION: LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('index'))

# ----------------- USER DASHBOARD -----------------
@app.route('/dashboard')
@login_required
def user_dashboard():
    user = db.session.get(User, session['user_id'])
    
    # User's uploaded notes
    my_notes = Note.query.filter_by(user_id=user.id).order_by(Note.created_at.desc()).all()
    
    # Download history with note details
    recent_downloads = DownloadHistory.query.filter_by(user_id=user.id)\
        .order_by(DownloadHistory.downloaded_at.desc()).limit(15).all()
        
    # Aggregate stats
    total_notes_uploaded = len(my_notes)
    total_downloads_received = sum(n.download_count for n in my_notes)
    total_views_received = sum(n.view_count for n in my_notes)
    
    return render_template('dashboard.html',
                           user=user,
                           my_notes=my_notes,
                           recent_downloads=recent_downloads,
                           total_notes_uploaded=total_notes_uploaded,
                           total_downloads_received=total_downloads_received,
                           total_views_received=total_views_received)

# ----------------- USER PROFILE UPDATE -----------------
@app.route('/dashboard/profile', methods=['POST'])
@login_required
def update_profile():
    user = db.session.get(User, session['user_id'])
    
    full_name = request.form.get('full_name', '').strip()
    department = request.form.get('department', '').strip()
    
    if not full_name:
        flash('Full Name is required.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    user.full_name = full_name
    user.department = department
    session['user_name'] = full_name
    
    db.session.commit()
    flash('Profile details updated successfully.', 'success')
    return redirect(url_for('user_dashboard'))

# ----------------- USER PASSWORD CHANGE -----------------
@app.route('/dashboard/change-password', methods=['POST'])
@login_required
def change_password():
    user = db.session.get(User, session['user_id'])
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_new_password = request.form.get('confirm_new_password', '')
    
    if not user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    if len(new_password) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    if new_password != confirm_new_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    user.set_password(new_password)
    db.session.commit()
    flash('Your password has been changed successfully.', 'success')
    return redirect(url_for('user_dashboard'))

# ----------------- ADMIN DASHBOARD -----------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Overall statistics
    total_users = User.query.count()
    total_notes = Note.query.count()
    total_downloads = db.session.query(db.func.sum(Note.download_count)).scalar() or 0
    total_views = db.session.query(db.func.sum(Note.view_count)).scalar() or 0
    
    # Calculate storage size in MB
    total_storage_bytes = db.session.query(db.func.sum(Note.file_size)).scalar() or 0
    storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
    
    # Manageable collections
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_notes = Note.query.order_by(Note.created_at.desc()).all()
    departments = Department.query.order_by(Department.name).all()
    
    return render_template('admin.html',
                           total_users=total_users,
                           total_notes=total_notes,
                           total_downloads=total_downloads,
                           total_views=total_views,
                           storage_mb=storage_mb,
                           users=all_users,
                           notes=all_notes,
                           departments=departments)

# Admin actions: Toggle User Status (ban/unban)
@app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session.get('user_id'):
        flash('You cannot deactivate your own admin account.', 'warning')
        return redirect(url_for('admin_dashboard'))
        
    user.is_active = not user.is_active
    db.session.commit()
    status_str = 'activated' if user.is_active else 'suspended'
    flash(f'User "{user.full_name}" has been {status_str}.', 'info')
    return redirect(url_for('admin_dashboard'))

# Admin actions: Toggle User Role
@app.route('/admin/users/<int:user_id>/toggle-role', methods=['POST'])
@admin_required
def admin_toggle_user_role(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session.get('user_id'):
        flash('You cannot change your own admin role.', 'warning')
        return redirect(url_for('admin_dashboard'))
        
    user.role = 'admin' if user.role != 'admin' else 'user'
    db.session.commit()
    flash(f'Role for "{user.full_name}" changed to {user.role.upper()}.', 'info')
    return redirect(url_for('admin_dashboard'))

# Admin actions: Delete User
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session.get('user_id'):
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    # Also clean up their physical files
    for note in user.notes:
        file_p = Config.UPLOAD_FOLDER / note.filename
        if file_p.exists():
            try:
                file_p.unlink()
            except OSError:
                pass
                
    db.session.delete(user)
    db.session.commit()
    flash(f'User account and all associated notes deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

# Admin actions: Toggle Featured
@app.route('/admin/notes/<int:note_id>/toggle-featured', methods=['POST'])
@admin_required
def admin_toggle_featured(note_id):
    note = db.get_or_404(Note, note_id)
    note.is_featured = not note.is_featured
    db.session.commit()
    status_str = 'featured' if note.is_featured else 'unfeatured'
    flash(f'Note "{note.title}" marked as {status_str}.', 'info')
    return redirect(url_for('admin_dashboard'))

# Admin actions: Add Department
@app.route('/admin/departments/add', methods=['POST'])
@admin_required
def admin_add_department():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    icon = request.form.get('icon', 'fa-book').strip()
    description = request.form.get('description', '').strip()
    
    if not name or not code:
        flash('Department Name and Code are required.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    if Department.query.filter((Department.name == name) | (Department.code == code)).first():
        flash('Department with this name or code already exists.', 'warning')
        return redirect(url_for('admin_dashboard'))
        
    new_dept = Department(name=name, code=code, icon=icon, description=description)
    db.session.add(new_dept)
    db.session.commit()
    flash(f'Department "{name}" added successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# Admin actions: Delete Department
@app.route('/admin/departments/<int:dept_id>/delete', methods=['POST'])
@admin_required
def admin_delete_department(dept_id):
    dept = db.get_or_404(Department, dept_id)
    # Check if notes are assigned
    count = Note.query.filter_by(department=dept.name).count()
    if count > 0:
        flash(f'Cannot delete department "{dept.name}" because it contains {count} notes. Reassign or delete notes first.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    db.session.delete(dept)
    db.session.commit()
    flash(f'Department "{dept.name}" has been deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

# ----------------- QUICK SEARCH API (JSON) -----------------
@app.route('/api/quick-search')
def quick_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])
        
    notes = Note.query.filter(
        Note.is_approved == True,
        (Note.title.ilike(f'%{q}%') | Note.subject.ilike(f'%{q}%'))
    ).limit(5).all()
    
    results = [
        {
            'id': n.id,
            'title': n.title,
            'subject': n.subject,
            'department': n.department,
            'semester': n.semester,
            'type': n.file_type.upper(),
            'url': url_for('note_detail', note_id=n.id)
        } for n in notes
    ]
    return jsonify(results)

# ----------------- ERROR HANDLERS -----------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template('413.html'), 413

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)
