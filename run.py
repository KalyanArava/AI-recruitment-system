"""
Smart AI Recruitment System — Entry Point
"""
import sys, os, subprocess

# ── Auto-install missing packages ──────────────────────────────
REQUIRED = [
    'flask', 'flask_sqlalchemy', 'flask_jwt_extended',
    'flask_mail', 'flask_cors', 'werkzeug',
    'pdfplumber', 'PyPDF2', 'scikit-learn', 'numpy'
]

print("🔍 Checking dependencies...")
missing = []
for pkg in REQUIRED:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"📦 Installing missing packages: {', '.join(missing)}")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
    print("✅ Packages installed!\n")
else:
    print("✅ All packages ready!\n")

# ── Set up paths ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND  = os.path.join(BASE_DIR, 'backend')

sys.path.insert(0, BACKEND)

from app import create_app

if __name__ == '__main__':
    app = create_app()

    print("\n" + "="*60)
    print("  🤖 Smart AI Recruitment — Glassmorphism UI")
    print("="*60)
    print("  🌐  http://localhost:5000")
    print("  🔐  admin@recruitment.com  /  Admin@123")
    print("="*60 + "\n")

    app.run(debug=True, port=5000, host='0.0.0.0')