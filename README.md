# 🌐 Live Website

**Visit Universal Notes Sharing Platform:**  
🔗 https://universal-note-sharing.onrender.com

---

# Universal Notes Sharing Platform 🎓📚

A modern, responsive, open-access educational web platform where university students and educators can upload, explore, search, preview, and download study notes, lecture summaries, and syllabus materials.

---

## 🌟 Key Features

### 1. 🌐 Public Open Access (No Mandatory Registration)

- **Zero Barriers to Learning:** Any visitor can freely browse, search, inspect full metadata, preview in-browser, and download published educational notes without needing to sign up or log in.
- **Registration Only When Contributing:** Account creation is required only when uploading or managing notes.

### 2. 🏛️ Modern Educational UI & Responsive Blue Theme

- **Color Theme:** Attractive academic blue and white design palette (`#1e40af`, `#2563eb`, `#eff6ff`) with clean shadows and typography (Inter and Plus Jakarta Sans).
- **Fully Responsive:** Optimized for mobile phones, tablets, and desktop workstations with an adaptive navigation drawer and grid layout.

### 3. 🔍 High-Performance Search & Multi-Filter Library

- **Live Search Bar:** Instant navbar auto-complete endpoint (`/api/quick-search?q=...`) with debounced querying.
- **Advanced Filtering:**
  - Search by title, subject, description, or keyword tags.
  - Filter by Academic Department / Faculty.
  - Filter by Semester (Semesters 1 through 8).
  - Filter by Document Format (PDF, Word DOCX/DOC, PowerPoint PPTX/PPT, Plain Text).
  - Sort by: Newest First, Most Downloaded, Most Viewed, Title (A-Z), Oldest.

### 4. 📄 In-Browser Document Preview & Tracked Downloads

- **Embedded PDF Viewer:** View PDF lecture notes directly in the browser with zoom and navigation controls.
- **Direct Download Engine:** Download notes with one click; downloads are automatically counted and logged into the audit history.
- **1-Click Share:** Copy shareable link directly to clipboard with visual toast feedback.

### 5. 📤 Secure File Upload & Verification

- **Drag-and-Drop Dropzone:** Intuitive file dropper with real-time file validation (extension and size checks).
- **Supported Formats:** `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.txt`.
- **Storage Protection:** Sanitized original filenames with cryptographically unique UUID prefixes to prevent directory traversal and file collisions.
- **Size Limits:** Configurable maximum upload size (default: 32 MB) with custom HTTP 413 error handling.

### 6. 📊 Student Dashboard

- **Performance Overview:** Total uploaded notes, total downloads received across your materials, and total views.
- **My Uploaded Notes:** Table of user's materials with direct View, Edit, and Delete actions.
- **Download History:** Audit log of all study materials downloaded by the student with 1-click re-download.
- **Profile & Security:** Update full name, major department, or securely change password.

### 7. 🛡️ Administrator Control Center

- **System Metrics:** Real-time statistics on total registered users, published notes, platform-wide downloads, and server storage consumed (MB).
- **Spam & Moderation Control:** Inspect any note and immediately remove unauthorized, low-quality, or spam material (permanently purging files from disk).
- **User Accounts Management:** Search users, toggle account status (Active / Suspended) to stop abusive uploaders, or promote students to administrators.
- **Category & Faculty Management:** Add new academic departments with custom codes and icons, or manage existing ones.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.x |
| **Database** | SQLite3 with Flask-SQLAlchemy |
| **Security** | Werkzeug PBKDF2 Password Hashing, Session Protection |
| **Frontend** | Semantic HTML5, CSS3 Variables, Responsive Flexbox & Grid |
| **Icons & Fonts** | Font Awesome 6, Google Fonts (Inter, Plus Jakarta Sans) |
| **Interactivity** | Vanilla JavaScript (ES6+), Fetch API, Drag-and-Drop API |

---

## 📁 Project Directory Structure

```text
notes sharing platform/
│
├── app.py                     # Main Flask application and RESTful routes
├── config.py                  # Application settings, secret keys, upload constraints
├── models.py                  # SQLAlchemy Database models (User, Note, Department, DownloadHistory)
├── init_db.py                 # Database initialization CLI script
├── seed_data.py               # Generates sample departments, demo accounts, and real notes files
├── test_app.py                # Comprehensive automated unit & integration test suite
├── requirements.txt           # Python package dependencies
├── README.md                  # Documentation and setup instructions
│
├── instance/
│   └── universal_notes.db     # SQLite database file
│
├── uploads/                   # Stored physical note files (PDF, DOCX, PPTX, etc.)
│
├── static/
│   ├── css/
│   │   ├── style.css          # Core theme, typography, responsive navbar, buttons, cards
│   │   └── dashboard.css      # User and Admin dashboards, metrics, modals, tables
│   ├── js/
│   │   ├── main.js            # Navbar toggle, auto-dismiss alerts, debounced search, share link
│   │   ├── upload.js          # Drag-and-drop validation, file preview, size check
│   │   └── dashboard.js       # Dashboard tab switching, modals, live table filtering
│   └── images/                # Static image assets
│
└── templates/
    ├── base.html              # Base layout with navbar, alerts, footer
    ├── index.html             # Home page (Hero, quick search, recent & popular notes, departments)
    ├── library.html           # Notes Library (Search & multi-filter, pagination, card grid)
    ├── note_detail.html       # Note Details (In-browser viewer, metadata, download CTA, related notes)
    ├── upload.html            # Upload Notes (Drag-and-drop file upload form)
    ├── edit_note.html         # Note edit metadata and file replacement form
    ├── login.html             # Login page with 1-click demo filler
    ├── register.html          # Registration page with validation
    ├── dashboard.html         # Student Dashboard (My notes, history, profile, password)
    ├── admin.html             # Admin Dashboard (Content moderation, user management, departments)
    ├── 404.html               # Custom 404 Page Not Found
    ├── 413.html               # Custom 413 File Exceeds Size Limit
    └── 500.html               # Custom 500 Internal Server Error
```

---

## 🚀 Installation & Quick Start Guide

### Step 1: Clone or Navigate to the Workspace

```powershell
cd "c:\Users\PRADEEP\Documents\notes sharing platform"
```

### Step 2: Install Dependencies

Ensure you have Python 3.10+ installed:

```powershell
pip install -r requirements.txt
```

### Step 3: Initialize & Seed the Database

Run the initialization script. This creates the SQLite database tables and seeds realistic sample notes (with genuine physical documents in `uploads/`):

```powershell
python init_db.py
```

### Step 4: Run the Web Application

```powershell
python app.py
```

The application will start locally at:

👉 **http://127.0.0.1:5000**

---

## 🔑 Default Demo Accounts

For quick demonstration and testing, the login page (`/login`) includes 1-click autofill buttons:

| Role | Email | Password | Access Capabilities |
|---|---|---|---|
| **Administrator** | `admin@universalnotes.com` | `Admin@123` | Full access to Admin Dashboard (`/admin`), user suspension, content moderation, category management. |
| **Student / Lecturer** | `sarah.mitchell@campus.edu` | `User@123` | Upload notes, manage own uploads in Student Dashboard (`/dashboard`), download history. |
| **Guest / Visitor** | *None required* | *None required* | Free access to browse, search, preview, and download all public notes. |

---

## 🧪 Running the Automated Test Suite

To verify that all features, security checks, and endpoints are operating correctly:

```powershell
python test_app.py
```

Expected output:

```text
.........
----------------------------------------------------------------------
Ran 9 tests in 2.1s

OK
```

---

## 🔒 Security & Performance Features

- **Password Protection:** Passwords are securely hashed using Werkzeug password hashing (PBKDF2/SHA256).
- **Directory Traversal Prevention:** Uploaded filenames are sanitized with `secure_filename()` and stored with unique UUID prefixes.
- **MIME & Extension Whitelisting:** Strict checks against allowed extensions (`.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.txt`).
- **File Size Guard:** Enforced `MAX_CONTENT_LENGTH = 32 MB` at both client and server layers.
- **Session Security:** `HttpOnly` and `SameSite='Lax'` cookies enabled.

---

## 🎯 Project Objective

The main objective of the Universal Notes Sharing Platform is to create a centralized educational resource where students and educators can easily share and access academic materials.

The platform reduces barriers to learning by providing free access to study resources, organized academic content, secure uploads, and an easy-to-use interface.

---

## 🌍 Live Project

**Universal Notes Sharing Platform**

🔗 https://universal-note-sharing.onrender.com

---

## 👨‍💻 Developed With

Built using Python, Flask, SQLite, HTML, CSS, and JavaScript to provide a simple, secure, and accessible educational notes-sharing experience.

**Made for students, by students. 🎓📚**
