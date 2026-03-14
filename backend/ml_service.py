from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import re

app = FastAPI(title="AI Resume Scoring Service")

model = SentenceTransformer("all-MiniLM-L6-v2")


class ScoreRequest(BaseModel):
    resume_text: str
    job_text: str


def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text


def tfidf_score(resume, job):

    vectorizer = TfidfVectorizer(stop_words='english')

    tfidf = vectorizer.fit_transform([resume, job])

    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]

    return score


def bert_score(resume, job):

    emb = model.encode([resume, job])

    score = cosine_similarity([emb[0]], [emb[1]])[0][0]

    return score


@app.post("/score")
def compute_score(data: ScoreRequest):

    resume = clean_text(data.resume_text)
    job = clean_text(data.job_text)

    tf = tfidf_score(resume, job)
    bt = bert_score(resume, job)

    final = (tf * 0.4) + (bt * 0.6)

    return {
        "tfidf_score": round(tf * 100, 2),
        "bert_score": round(bt * 100, 2),
        "match_percentage": round(final * 100, 2)
    }