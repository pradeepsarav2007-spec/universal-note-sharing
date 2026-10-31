import os
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

from config import Config
from models import db, User, Department, Note, DownloadHistory
from app import app

def generate_minimal_pdf(file_path: Path, title: str, subject: str, notes_content: str):
    """Generates a valid standard PDF 1.4 file with educational content"""
    # Sanitize content for PDF stream
    clean_title = title.replace('(', '').replace(')', '')
    clean_subject = subject.replace('(', '').replace(')', '')
    
    stream_content = f"""BT
/F1 20 Tf
50 720 Td
({clean_title}) Tj
/F1 12 Tf
0 -30 Td
(Subject: {clean_subject}) Tj
0 -20 Td
(Universal Notes Sharing Platform - Educational Repository) Tj
0 -30 Td
(-----------------------------------------------------------------------------------) Tj
0 -30 Td
(LECTURE NOTES & SUMMARY:) Tj
"""
    # Add body lines
    y_offset = -20
    lines = notes_content.split('\n')
    for line in lines[:25]:
        line = line.strip().replace('(', '[').replace(')', ']')
        if line:
            stream_content += f"0 {y_offset} Td\n({line[:75]}) Tj\n"
            y_offset = -18
            
    stream_content += "\nET\n"
    stream_len = len(stream_content.encode('latin1'))

    pdf_structure = f"""%PDF-1.4
1 0 obj
<<
  /Type /Catalog
  /Pages 2 0 R
>>
endobj
2 0 obj
<<
  /Type /Pages
  /Kids [3 0 R]
  /Count 1
>>
endobj
3 0 obj
<<
  /Type /Page
  /Parent 2 0 R
  /MediaBox [0 0 612 792]
  /Contents 4 0 R
  /Resources <<
    /Font <<
      /F1 5 0 R
    >>
  >>
>>
endobj
4 0 obj
<<
  /Length {stream_len}
>>
stream
{stream_content}
endstream
endobj
5 0 obj
<<
  /Type /Font
  /Subtype /Type1
  /BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000373 00000 n 
trailer
<<
  /Size 6
  /Root 1 0 R
>>
startxref
465
%%EOF
"""
    with open(file_path, 'wb') as f:
        f.write(pdf_structure.encode('latin1'))

def generate_sample_doc(file_path: Path, title: str, subject: str, notes_content: str):
    """Generates a text/formatted notes document"""
    header = f"="*80 + f"\nUNIVERSAL NOTES SHARING PLATFORM\nTITLE: {title}\nSUBJECT: {subject}\n" + "="*80 + "\n\n"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header + notes_content)

def seed_database():
    with app.app_context():
        # Ensure uploads folder
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
        print("Creating all database tables...")
        db.create_all()

        # 1. Seed Departments
        departments_data = [
            {
                "name": "Computer Science & Engineering",
                "code": "CSE",
                "icon": "fa-laptop-code",
                "description": "Algorithms, Data Structures, Operating Systems, AI, Web Dev & Cloud Computing."
            },
            {
                "name": "Electrical & Electronics",
                "code": "EEE",
                "icon": "fa-bolt",
                "description": "Circuit Analysis, Microcontrollers, Signal Processing, Power Systems & Robotics."
            },
            {
                "name": "Mechanical Engineering",
                "code": "MECH",
                "icon": "fa-gears",
                "description": "Thermodynamics, Fluid Mechanics, Kinematics, CAD/CAM & Machine Design."
            },
            {
                "name": "Civil Engineering",
                "code": "CIVIL",
                "icon": "fa-building-columns",
                "description": "Structural Analysis, Concrete Technology, Surveying & Geotechnical Engg."
            },
            {
                "name": "Business & Management",
                "code": "MBA",
                "icon": "fa-chart-line",
                "description": "Financial Accounting, Marketing Strategy, Human Resources & Operations Research."
            },
            {
                "name": "Medical & Health Sciences",
                "code": "MED",
                "icon": "fa-stethoscope",
                "description": "Human Anatomy, Biochemistry, Pharmacology, Pathology & Clinical Medicine."
            },
            {
                "name": "Mathematics & Physics",
                "code": "SCI",
                "icon": "fa-atom",
                "description": "Calculus, Linear Algebra, Quantum Physics, Mechanics & Differential Equations."
            }
        ]

        departments_map = {}
        for dept in departments_data:
            existing = Department.query.filter_by(code=dept['code']).first()
            if not existing:
                dept_obj = Department(**dept)
                db.session.add(dept_obj)
                db.session.flush()
                departments_map[dept['name']] = dept_obj
            else:
                departments_map[dept['name']] = existing

        db.session.commit()
        print(f"Departments initialized ({len(departments_map)} departments).")

        # 2. Seed Users
        # Admin user
        admin = User.query.filter_by(email="admin@universalnotes.com").first()
        if not admin:
            admin = User(
                full_name="Platform Administrator",
                email="admin@universalnotes.com",
                department="Computer Science & Engineering",
                role="admin",
                is_active=True
            )
            admin.set_password("Admin@123")
            db.session.add(admin)
            print("Admin user created: admin@universalnotes.com / Admin@123")

        # Demo Students
        demo_users_data = [
            ("Dr. Sarah Mitchell", "sarah.mitchell@campus.edu", "Computer Science & Engineering", "User@123"),
            ("Alex Chen", "alex.chen@campus.edu", "Electrical & Electronics", "User@123"),
            ("Priya Patel", "priya.patel@campus.edu", "Business & Management", "User@123"),
            ("David Kim", "david.kim@campus.edu", "Mathematics & Physics", "User@123"),
        ]

        users_map = {}
        for name, email, dept, pwd in demo_users_data:
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(
                    full_name=name,
                    email=email,
                    department=dept,
                    role="user",
                    is_active=True
                )
                u.set_password(pwd)
                db.session.add(u)
                db.session.flush()
            users_map[email] = u

        db.session.commit()
        print("Users initialized.")

        # 3. Seed Realistic Educational Notes
        sample_notes_data = [
            {
                "title": "Data Structures & Algorithms Comprehensive Lecture Notes",
                "subject": "Data Structures & Algorithms",
                "department": "Computer Science & Engineering",
                "semester": 3,
                "description": "In-depth study guide covering Arrays, Linked Lists, Balanced Binary Trees (AVL, Red-Black), Graphs (BFS, DFS, Dijkstra), Dynamic Programming, and Big-O Space/Time complexity analysis with pseudo-code implementations.",
                "tags": "DSA, Algorithms, Trees, Graphs, Sorting, Dynamic Programming",
                "uploader_email": "sarah.mitchell@campus.edu",
                "format": "pdf",
                "downloads": 142,
                "views": 489,
                "featured": True,
                "days_ago": 2
            },
            {
                "title": "Operating Systems & Concurrency Cheat Sheet",
                "subject": "Operating Systems",
                "department": "Computer Science & Engineering",
                "semester": 4,
                "description": "Complete breakdown of process scheduling, semaphores, mutex locks, thread synchronization, deadlocks detection and prevention (Banker's Algorithm), virtual memory, page replacement algorithms, and file systems.",
                "tags": "Operating Systems, Concurrency, Deadlock, Threads, Virtual Memory",
                "uploader_email": "sarah.mitchell@campus.edu",
                "format": "pdf",
                "downloads": 98,
                "views": 310,
                "featured": True,
                "days_ago": 4
            },
            {
                "title": "Digital Signal Processing & Fourier Transforms",
                "subject": "Signals & Systems",
                "department": "Electrical & Electronics",
                "semester": 5,
                "description": "Comprehensive study notes covering Discrete Fourier Transform (DFT), Fast Fourier Transform (FFT), Z-Transform, FIR and IIR digital filter design with MATLAB simulation examples and transfer function equations.",
                "tags": "DSP, Fourier Transform, FFT, Filter Design, MATLAB",
                "uploader_email": "alex.chen@campus.edu",
                "format": "pdf",
                "downloads": 76,
                "views": 215,
                "featured": False,
                "days_ago": 6
            },
            {
                "title": "Thermodynamics & Heat Transfer Fundamentals",
                "subject": "Applied Thermodynamics",
                "department": "Mechanical Engineering",
                "semester": 3,
                "description": "Detailed notes on Laws of Thermodynamics, Carnot Cycle, Rankine and Brayton cycles, conduction, convection, radiation heat transfer coefficients, and entropy diagrams for mechanical engineers.",
                "tags": "Thermodynamics, Heat Transfer, Entropy, Carnot Cycle, Energy",
                "uploader_email": "alex.chen@campus.edu",
                "format": "docx",
                "downloads": 64,
                "views": 180,
                "featured": False,
                "days_ago": 8
            },
            {
                "title": "Financial Accounting & Corporate Valuation Models",
                "subject": "Corporate Finance",
                "department": "Business & Management",
                "semester": 2,
                "description": "Detailed guide on Balance Sheet analysis, Income Statements, Cash Flow ratios, DCF (Discounted Cash Flow) valuation, WACC computation, and investment capital budgeting techniques.",
                "tags": "Finance, Accounting, DCF, Balance Sheet, Valuation, MBA",
                "uploader_email": "priya.patel@campus.edu",
                "format": "pdf",
                "downloads": 115,
                "views": 390,
                "featured": True,
                "days_ago": 3
            },
            {
                "title": "Human Neuroanatomy & Cranial Nerves Illustrated Notes",
                "subject": "Human Anatomy",
                "department": "Medical & Health Sciences",
                "semester": 1,
                "description": "Illustrated medical study notes examining the 12 cranial nerves, pathways, motor vs sensory functions, brainstem divisions, clinical examination reflexes, and common neurological lesions.",
                "tags": "Medicine, Anatomy, Neuroanatomy, Cranial Nerves, Brain",
                "uploader_email": "david.kim@campus.edu",
                "format": "pdf",
                "downloads": 130,
                "views": 412,
                "featured": True,
                "days_ago": 5
            },
            {
                "title": "Multivariable Calculus & Vector Fields Study Pack",
                "subject": "Calculus III",
                "department": "Mathematics & Physics",
                "semester": 2,
                "description": "Partial derivatives, Lagrange multipliers, double and triple integrals in cylindrical and spherical coordinates, line integrals, Green's Theorem, Stokes' Theorem, and Divergence Theorem with solved problems.",
                "tags": "Calculus, Mathematics, Green Theorem, Stokes Theorem, Vectors",
                "uploader_email": "david.kim@campus.edu",
                "format": "pdf",
                "downloads": 88,
                "views": 260,
                "featured": False,
                "days_ago": 7
            },
            {
                "title": "Structural Analysis & Reinforced Concrete Design Handout",
                "subject": "Structural Engineering",
                "department": "Civil Engineering",
                "semester": 4,
                "description": "Bending moment and shear force diagrams for indeterminate beams, slope deflection method, moment distribution method, limit state design for RCC beams, columns, and slabs according to building codes.",
                "tags": "Civil, Structural Analysis, RCC, Beams, Concrete, Shear Force",
                "uploader_email": "alex.chen@campus.edu",
                "format": "docx",
                "downloads": 52,
                "views": 175,
                "featured": False,
                "days_ago": 10
            },
            {
                "title": "Database Management Systems & SQL Query Optimization",
                "subject": "DBMS",
                "department": "Computer Science & Engineering",
                "semester": 4,
                "description": "Relational algebra, ER diagrams, Normalization (1NF, 2NF, 3NF, BCNF), Transaction ACID properties, concurrency control (2PL, Timestamping), and B-Tree indexing query optimization.",
                "tags": "Database, SQL, Normalization, ACID, Indexes, CSE",
                "uploader_email": "sarah.mitchell@campus.edu",
                "format": "pptx",
                "downloads": 105,
                "views": 340,
                "featured": False,
                "days_ago": 1
            }
        ]

        for item in sample_notes_data:
            existing_note = Note.query.filter_by(title=item["title"]).first()
            if existing_note:
                continue

            # Determine uploader
            uploader = users_map.get(item["uploader_email"], admin)
            dept_obj = departments_map.get(item["department"])

            # Generate real file on disk
            raw_filename = f"{item['subject'].replace(' ', '_').lower()}_notes.{item['format']}"
            unique_filename = f"{uuid.uuid4().hex[:12]}_{raw_filename}"
            file_path = Config.UPLOAD_FOLDER / unique_filename

            # Create file
            content_sample = f"""TOPIC: {item['title']}
SUBJECT: {item['subject']}
DEPARTMENT: {item['department']} - SEMESTER {item['semester']}
AUTHORS: {uploader.full_name}

OVERVIEW & OBJECTIVES:
{item['description']}

KEY CONCEPTS COVERED:
1. Fundamental theoretical models and analytical frameworks.
2. Step-by-step problem solving methodology and worked examples.
3. Industry and laboratory standard implementations.
4. Review questions, exam preparation pointers, and reference citations.

SUMMARY:
These comprehensive notes are prepared to support university students and lifelong learners
across all departments. Accessible freely via the Universal Notes Sharing Platform.
"""
            if item['format'] == 'pdf':
                generate_minimal_pdf(file_path, item['title'], item['subject'], content_sample)
            else:
                generate_sample_doc(file_path, item['title'], item['subject'], content_sample)

            file_size = file_path.stat().st_size
            created_time = datetime.now(timezone.utc) - timedelta(days=item['days_ago'])

            note = Note(
                title=item['title'],
                subject=item['subject'],
                department=item['department'],
                department_id=dept_obj.id if dept_obj else None,
                semester=item['semester'],
                description=item['description'],
                tags=item['tags'],
                filename=unique_filename,
                original_filename=raw_filename,
                file_type=item['format'],
                file_size=file_size,
                user_id=uploader.id,
                download_count=item['downloads'],
                view_count=item['views'],
                is_approved=True,
                is_featured=item['featured'],
                created_at=created_time,
                updated_at=created_time
            )
            db.session.add(note)

        db.session.commit()
        print("Sample notes successfully seeded with genuine physical document files!")

if __name__ == '__main__':
    seed_database()
