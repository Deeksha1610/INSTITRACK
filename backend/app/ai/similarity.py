"""
AI-assisted related case detection using TF-IDF and cosine similarity.
Local, no paid APIs required.
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.case import Case, RelatedCase
from app.core.config import settings


def find_related_cases(
    db: Session,
    source_case: Case,
    top_k: int = 5,
    threshold: Optional[float] = None,
) -> List[Tuple[Case, float]]:
    """
    Find potentially related cases based on title + description similarity.
    Returns list of (case, similarity_score) sorted by score descending.
    """
    threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

    candidates = (
        db.query(Case)
        .filter(Case.id != source_case.id)
        .filter(Case.status != "REJECTED")  # still compare text
        .all()
    )
    if not candidates:
        return []

    source_text = f"{source_case.title} {source_case.description}"
    candidate_texts = [f"{c.title} {c.description}" for c in candidates]

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
        all_texts = [source_text] + candidate_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        source_vec = tfidf_matrix[0:1]
        candidate_vecs = tfidf_matrix[1:]
        scores = cosine_similarity(source_vec, candidate_vecs).flatten()
    except Exception:
        return []

    results = []
    for idx, score in enumerate(scores):
        if score >= threshold:
            results.append((candidates[idx], float(score)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def persist_suggestion(
    db: Session,
    source_case_id: int,
    target_case_id: int,
    score: float,
) -> RelatedCase:
    existing = (
        db.query(RelatedCase)
        .filter(
            RelatedCase.source_case_id == source_case_id,
            RelatedCase.target_case_id == target_case_id,
        )
        .first()
    )
    if existing:
        existing.similarity_score = score
        return existing

    rel = RelatedCase(
        source_case_id=source_case_id,
        target_case_id=target_case_id,
        similarity_score=score,
        confirmed=False,
    )
    db.add(rel)
    return rel
