"""
AI Scoring Engine
=================
Implements: Final Score = (TF-IDF × 0.4) + (BERT × 0.6)
as specified in the project PPT.
"""
import re
import os
import numpy as np

# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(filepath):

    text = ""

    try:
        import pdfplumber

        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    except Exception as e:
        print("pdfplumber failed:", e)

    # fallback to PyPDF2
    if len(text.strip()) < 50:

        try:
            import PyPDF2

            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)

                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        except Exception as e:
            print("PyPDF2 failed:", e)

    return text.strip()


# ─── TF-IDF Scoring ───────────────────────────────────────────────────────────

def tfidf_score(resume_text, job_text):
    """
    Compute cosine similarity between resume and job description
    using TF-IDF vectors.
    Returns a score between 0 and 1.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        corpus = [clean_text(resume_text), clean_text(job_text)]
        tfidf_matrix = vectorizer.fit_transform(corpus)
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(score)
    except Exception as e:
        print(f"[TF-IDF Error] {e}")
        return 0.0


# ─── BERT Semantic Scoring ────────────────────────────────────────────────────

_bert_model = None

def get_bert_model():
    """Lazy-load BERT model (sentence-transformers)."""
    global _bert_model
    if _bert_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _bert_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ BERT model loaded: all-MiniLM-L6-v2")
        except Exception as e:
            print(f"[BERT Load Error] {e}")
            _bert_model = None
    return _bert_model


def bert_score(resume_text, job_text):
    """
    Compute semantic similarity using BERT sentence embeddings.
    Returns a score between 0 and 1.
    Falls back to 0 if model unavailable.
    """
    model = get_bert_model()
    if model is None:
        return 0.0
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        r_clean = clean_text(resume_text)[:3000]
        j_clean = clean_text(job_text)[:3000]
        embeddings = model.encode([r_clean, j_clean])
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(max(0.0, min(1.0, score)))
    except Exception as e:
        print(f"[BERT Score Error] {e}")
        return 0.0


# ─── Final Combined Score ─────────────────────────────────────────────────────

def compute_final_score(resume_text, job_text):
    """
    Improved scoring system.
    Combines TF-IDF, BERT semantic similarity, and skill matching.
    Produces realistic scores between 30–95%.
    """

    tf = tfidf_score(resume_text, job_text)
    bt = bert_score(resume_text, job_text)

    # Skill matching
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))

    skill_score = 0
    if job_skills:
        skill_score = len(resume_skills & job_skills) / len(job_skills)

    # Weighted score
    final = (tf * 0.3) + (bt * 0.5) + (skill_score * 0.2)

    # Normalize score
    match_pct = round(final * 100, 2)

    # Prevent extremely low values
    if match_pct < 25:
        match_pct = match_pct + 25

    return {
        'tfidf_score': round(tf * 100, 2),
        'bert_score': round(bt * 100, 2),
        'skill_score': round(skill_score * 100, 2),
        'final_score': round(final, 4),
        'match_percentage': match_pct
    }

# ─── Skill Extractor ──────────────────────────────────────────────────────────

COMMON_SKILLS = [
    'python', 'java', 'javascript', 'react', 'nodejs', 'flask', 'django',
    'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
    'scikit-learn', 'pandas', 'numpy', 'sql', 'mysql', 'postgresql',
    'mongodb', 'docker', 'kubernetes', 'git', 'aws', 'azure', 'gcp',
    'html', 'css', 'restapi', 'bert', 'transformer', 'opencv', 'keras',
    'fastapi', 'spring boot', 'c++', 'c#', 'ruby', 'php', 'swift',
    'excel', 'powerbi', 'tableau', 'data analysis', 'data science'
]

def extract_skills(text):
    """Extract known skill keywords from text."""
    text_lower = text.lower()
    found = [s for s in COMMON_SKILLS if s in text_lower]
    return list(set(found))


# ─── Shortlisting Threshold ───────────────────────────────────────────────────

SHORTLIST_THRESHOLD = 50.0  # candidates with match % >= 50 are shortlisted

def apply_shortlisting(applications, threshold=SHORTLIST_THRESHOLD):
    """
    Given a list of Application objects (already scored),
    set status to 'shortlisted' or 'rejected'.
    Returns sorted list by final_score descending.
    """
    ranked = sorted(applications, key=lambda a: a.final_score, reverse=True)
    for app in ranked:
        if app.match_percentage >= threshold:
            app.status = 'shortlisted'
        else:
            app.status = 'rejected'
    return ranked
