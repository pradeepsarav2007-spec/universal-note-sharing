import unittest
import io
import os
from pathlib import Path

from config import Config
from app import app
from models import db, User, Department, Note, DownloadHistory

class UniversalNotesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key-1234'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

            # Idempotently fetch or create test department
            self.dept = Department.query.filter_by(code="CSE_TEST").first()
            if not self.dept:
                self.dept = Department(
                    name="Test Computer Science",
                    code="CSE_TEST",
                    icon="fa-laptop-code",
                    description="CS curriculum testing"
                )
                db.session.add(self.dept)
                db.session.commit()

            # Idempotently fetch or create admin user
            self.admin = User.query.filter_by(email="admin_unit@test.com").first()
            if not self.admin:
                self.admin = User(
                    full_name="Admin Unit Tester",
                    email="admin_unit@test.com",
                    department=self.dept.name,
                    role="admin",
                    is_active=True
                )
                self.admin.set_password("AdminPass123")
                db.session.add(self.admin)
                db.session.commit()

            # Idempotently fetch or create regular student user
            self.student = User.query.filter_by(email="student_unit@test.com").first()
            if not self.student:
                self.student = User(
                    full_name="John Doe",
                    email="student_unit@test.com",
                    department=self.dept.name,
                    role="user",
                    is_active=True
                )
                self.student.set_password("StudentPass123")
                db.session.add(self.student)
                db.session.commit()

            # Ensure upload folder exists and create test file
            Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            self.test_filename = "unit_test_sample.pdf"
            test_file_path = Config.UPLOAD_FOLDER / self.test_filename
            with open(test_file_path, "wb") as f:
                f.write(b"%PDF-1.4 Minimal test pdf content for unit tests")

            # Create test note
            self.note = Note.query.filter_by(title="Algorithms and Data Structures Guide").first()
            if not self.note:
                self.note = Note(
                    title="Algorithms and Data Structures Guide",
                    subject="Data Structures",
                    department=self.dept.name,
                    department_id=self.dept.id,
                    semester=3,
                    description="Comprehensive test study guide for trees and graphs.",
                    tags="algorithms, graphs, trees",
                    filename=self.test_filename,
                    original_filename="sample_guide.pdf",
                    file_type="pdf",
                    file_size=len(b"%PDF-1.4 Minimal test pdf content for unit tests"),
                    user_id=self.student.id,
                    download_count=5,
                    view_count=12,
                    is_approved=True
                )
                db.session.add(self.note)
                db.session.commit()
            self.note_id = self.note.id

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Universal", response.data)
        self.assertIn(b"Algorithms and Data Structures Guide", response.data)

    def test_library_public_access_and_filters(self):
        # 1. Unauthenticated guest can access library
        response = self.client.get('/library')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Universal Notes Library", response.data)

        # 2. Search by keyword
        res_search = self.client.get('/library?q=Algorithms')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b"Algorithms and Data Structures Guide", res_search.data)

        # 3. Filter by department
        res_dept = self.client.get(f'/library?department={self.dept.name}')
        self.assertEqual(res_dept.status_code, 200)
        self.assertIn(b"Data Structures", res_dept.data)

        # 4. Filter by semester
        res_sem = self.client.get('/library?semester=3')
        self.assertEqual(res_sem.status_code, 200)
        self.assertIn(b"Semester 3", res_sem.data)

    def test_note_detail_and_view_count(self):
        with app.app_context():
            initial_views = db.session.get(Note, self.note_id).view_count

        response = self.client.get(f'/notes/{self.note_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Algorithms and Data Structures Guide", response.data)

        with app.app_context():
            updated_note = db.session.get(Note, self.note_id)
            self.assertEqual(updated_note.view_count, initial_views + 1)

    def test_note_download_public(self):
        with app.app_context():
            initial_downloads = db.session.get(Note, self.note_id).download_count

        # Guest can download note
        response = self.client.get(f'/notes/{self.note_id}/download')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename=sample_guide.pdf')
        response.close()

        with app.app_context():
            updated_note = db.session.get(Note, self.note_id)
            self.assertEqual(updated_note.download_count, initial_downloads + 1)
            # Verify download history entry logged
            history = DownloadHistory.query.filter_by(note_id=self.note_id).first()
            self.assertIsNotNone(history)

    def test_user_registration(self):
        unique_email = f"alice_{os.urandom(4).hex()}@test.com"
        response = self.client.post('/register', data={
            'full_name': 'Alice Wonder',
            'email': unique_email,
            'department': self.dept.name,
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        with app.app_context():
            user = User.query.filter_by(email=unique_email).first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password('Password123'))

    def test_user_login_and_logout(self):
        # Login with correct credentials
        res_login = self.client.post('/login', data={
            'email': 'student_unit@test.com',
            'password': 'StudentPass123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Welcome back", res_login.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b"logged out", res_logout.data)

    def test_authenticated_note_upload(self):
        # Login as student first
        self.client.post('/login', data={'email': 'student_unit@test.com', 'password': 'StudentPass123'})

        title = f"Calculus II Integration {os.urandom(3).hex()}"
        fake_file = (io.BytesIO(b"%PDF-1.4 Test note upload stream"), 'calculus_cheat_sheet.pdf')
        res_upload = self.client.post('/upload', data={
            'title': title,
            'subject': 'Calculus II',
            'department': self.dept.name,
            'semester': '2',
            'description': 'Integration by parts, partial fractions, and trigonometric substitutions.',
            'tags': 'calculus, integration',
            'file': fake_file
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(res_upload.status_code, 200)
        self.assertIn(title.encode(), res_upload.data)

        with app.app_context():
            new_note = Note.query.filter_by(title=title).first()
            self.assertIsNotNone(new_note)
            self.assertEqual(new_note.semester, 2)
            # Verify file exists on disk
            uploaded_file = Config.UPLOAD_FOLDER / new_note.filename
            self.assertTrue(uploaded_file.exists())
            # Clean up
            uploaded_file.unlink()
            db.session.delete(new_note)
            db.session.commit()

    def test_admin_dashboard_access_control(self):
        # 1. Guest access should redirect to login
        res_guest = self.client.get('/admin')
        self.assertEqual(res_guest.status_code, 302)

        # 2. Regular student access should be forbidden / redirected with error
        self.client.post('/login', data={'email': 'student_unit@test.com', 'password': 'StudentPass123'})
        res_student = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b"Access denied", res_student.data)

        # 3. Admin user access succeeds
        self.client.get('/logout')
        self.client.post('/login', data={'email': 'admin_unit@test.com', 'password': 'AdminPass123'})
        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Administrator Control Center", res_admin.data)

    def test_quick_search_api(self):
        response = self.client.get('/api/quick-search?q=Algo')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        titles = [item['title'] for item in data]
        self.assertTrue(any('algo' in t.lower() for t in titles))

if __name__ == '__main__':
    unittest.main()
