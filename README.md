<<<<<<< HEAD
# 🤖 Smart AI Recruitment System
### AI-Powered Hiring with NLP & Deep Learning | Glassmorphism UI

---

## 🚀 Quick Start (VS Code)

### Step 1 — Install Python packages
```bash
pip install -r requirements.txt
```

> ⚠️ For BERT (best AI accuracy), also run:
> ```bash
> pip install sentence-transformers torch
> ```
> Without it, the system still works using TF-IDF alone.

---

### Step 2 — (Optional) Configure Email

Open `backend/app.py` and set your Gmail credentials:
```python
app.config['MAIL_USERNAME'] = 'your_gmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_gmail_app_password'
```

> **Get Gmail App Password**: Google Account → Security → 2-Step Verification → App Passwords

> **Skip email?** The OTP is shown in the API response (`dev_otp` field) and as a toast notification in dev mode.

---

### Step 3 — Run the server
```bash
python run.py
```

Open browser: **http://localhost:5000**

---

## 🔐 Default Login

| Role     | Email                     | Password    |
|----------|---------------------------|-------------|
| Admin    | admin@recruitment.com     | Admin@123   |
| Recruiter| Register a new account    | —           |
| Candidate| Register a new account    | —           |

---

## 📁 Project Structure

```
smart_recruitment/
├── run.py                          ← Entry point
├── requirements.txt
├── backend/
│   ├── app.py                      ← Flask app factory
│   ├── models/
│   │   ├── user.py                 ← User model
│   │   └── models.py               ← Job, Resume, Application, AuditLog
│   ├── routes/
│   │   ├── auth.py                 ← Register, Login, OTP, Reset
│   │   ├── admin.py                ← Admin CRUD
│   │   ├── recruiter.py            ← Jobs, Upload, AI screening
│   │   ├── candidate.py            ← Browse, Apply, Dashboard
│   │   ├── ml_routes.py            ← AI scoring API
│   │   └── pages.py                ← HTML page routes
│   ├── ml/
│   │   └── scorer.py               ← TF-IDF + BERT scoring engine
│   └── uploads/                    ← Uploaded PDF resumes
└── frontend/
    ├── templates/
    │   ├── login.html
    │   ├── register.html
    │   ├── verify_otp.html
    │   ├── forgot_password.html
    │   ├── admin.html
    │   ├── recruiter.html
    │   ├── candidate.html
    │   └── ml_dashboard.html
    └── static/
        ├── css/
        │   └── glass.css           ← Full glassmorphism design system
        └── js/
            └── glass-app.js        ← Global JS utilities
```

---

## 🧠 AI Scoring Formula

```
Final Score = (TF-IDF Score × 0.4) + (BERT Score × 0.6)
Match % = Final Score × 100
Shortlisted if Match % ≥ 50%
```

---

## 📄 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login |
| POST | /api/auth/verify-otp | Verify email OTP |
| POST | /api/auth/forgot-password | Send reset OTP |
| POST | /api/auth/reset-password | Reset password |

### Recruiter
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/recruiter/jobs | List my jobs |
| POST | /api/recruiter/jobs | Create job |
| PUT | /api/recruiter/jobs/:id | Update job |
| DELETE | /api/recruiter/jobs/:id | Delete job |
| POST | /api/recruiter/jobs/:id/upload-resumes | Bulk upload & AI score |
| GET | /api/recruiter/jobs/:id/results | View ranked results |
| GET | /api/recruiter/jobs/:id/download-shortlist | ZIP download |

### Candidate
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/candidate/jobs | Browse open jobs |
| POST | /api/candidate/upload-resume | Upload PDF resume |
| POST | /api/candidate/apply/:job_id | Apply to job |
| GET | /api/candidate/my-applications | View applications |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/dashboard | Stats |
| GET | /api/admin/users | All users |
| POST | /api/admin/users/:id/toggle | Enable/disable user |
| POST | /api/admin/promote | Change role |
| GET | /api/admin/audit-logs | System logs |

---

## 🎨 UI Pages

| Page | URL | Access |
|------|-----|--------|
| Login | /login | Public |
| Register | /register | Public |
| Verify OTP | /verify-otp | Public |
| Forgot Password | /forgot-password | Public |
| Admin Dashboard | /admin | Admin only |
| Recruiter Dashboard | /recruiter | Recruiter |
| Candidate Dashboard | /candidate | Candidate |

---

## ⚙️ Troubleshooting

**Port already in use:**
```bash
python run.py  # changes port to 5001 if needed
```

**BERT model slow to load (first time):**
> Normal — it downloads ~90MB model on first run. Subsequent runs are instant.

**SQLite database reset:**
```bash
rm backend/recruitment.db
python run.py  # re-creates with fresh admin
```
=======
# AI-recruitment-system
# 🧠 AI Recruitment System

An intelligent recruitment platform that uses AI to analyze resumes and match candidates with job descriptions.

## 🚀 Features
- AI Resume Scoring (TF-IDF + BERT)
- Candidate Ranking
- Job Recommendation System
- Resume Skill Extraction
- Admin Analytics Dashboard
- Email OTP Authentication

## ⚙️ Installation

Clone the repository:

git clone https://github.com/KalyanArava/AI-recruitment-system.git

Install dependencies:

pip install -r requirements.txt

Run the project:

python run.py
>>>>>>> 45756cf011322345ae11ed74f069d806f049d6c1
