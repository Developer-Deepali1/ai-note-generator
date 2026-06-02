"""NLP engine for transcript cleaning, extraction and summarization.

Examples:
    >>> result = summarize_transcript('We should send the report tomorrow. Alice will own it.')
    >>> bool(result['summary'])
    True
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any

from utils.constants import DEFAULT_LANGUAGE

STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were',
    'you', 'your', 'they', 'them', 'their', 'about', 'into', 'will', 'shall', 'than',
    'been', 'there', 'here', 'when', 'what', 'where', 'which', 'would', 'could', 'should',
    'need', 'todo', 'also', 'while', 'over', 'under', 'after', 'before', 'more', 'most',
    'some', 'such', 'has', 'had', 'not', 'can', 'may', 'might', 'one', 'all', 'any',
    'our', 'out', 'use', 'used', 'using', 'session', 'note', 'notes',
}

_ACTION_PATTERNS = (
    r'\b(action item|follow up|next step|todo|to do|need to|must|should)\b',
    r'\b(assign(?:ed)?\s+to|owner(?:ship)?\s*[:\-])\b',
)


def _clean_text(text: str) -> str:
    normalized = unicodedata.normalize('NFKC', text or '')
    normalized = re.sub(r'[\u200B-\u200D\uFEFF]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def _split_sentences(text: str) -> list[str]:
    return [segment.strip() for segment in re.split(r'(?<=[.!?])\s+|\n+', text) if segment.strip()]


def _extract_keywords(text: str, *, max_items: int = 10) -> list[dict[str, Any]]:
    words = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'-]+", text)]
    filtered = [word for word in words if word not in STOPWORDS and len(word) > 2]
    counts = Counter(filtered)
    total = sum(counts.values()) or 1
    return [
        {
            'keyword': word,
            'count': count,
            'frequency': round(count / total, 4),
            'confidence': round(min(1.0, 0.55 + (count / total)), 3),
        }
        for word, count in counts.most_common(max_items)
    ]


def _extract_named_entities(text: str) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    try:  # pragma: no cover - depends on external model availability
        import spacy

        model = None
        for candidate in ('en_core_web_sm', 'xx_ent_wiki_sm'):
            try:
                model = spacy.load(candidate)
                break
            except Exception:
                continue
        if model is not None:
            doc = model(text)
            entities = [
                {
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.85,
                }
                for ent in doc.ents
            ]
    except Exception:
        entities = []

    if entities:
        return entities

    fallback = sorted(set(re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*\b', text)))
    return [
        {
            'text': token,
            'label': 'PROPN',
            'start': text.find(token),
            'end': text.find(token) + len(token),
            'confidence': 0.5,
        }
        for token in fallback[:10]
    ]


def _extract_action_items(sentences: list[str]) -> list[dict[str, Any]]:
    action_items: list[dict[str, Any]] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if not any(re.search(pattern, lowered) for pattern in _ACTION_PATTERNS):
            continue
        assignee_match = re.search(r'\b([A-Z][a-z]+)\s+(?:will|should|must|can)\b', sentence)
        action_items.append(
            {
                'task': sentence,
                'assignee': assignee_match.group(1) if assignee_match else None,
                'confidence': 0.85 if assignee_match else 0.7,
            }
        )
    return action_items[:10]


def _summarize(sentences: list[str], *, max_sentences: int = 3) -> tuple[str, list[str]]:
    if not sentences:
        return 'No transcript was provided.', []

    token_counts = Counter(
        token.lower()
        for sentence in sentences
        for token in re.findall(r"[A-Za-z][A-Za-z'-]+", sentence)
        if token.lower() not in STOPWORDS
    )
    scores: list[tuple[float, str]] = []
    for sentence in sentences:
        tokens = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'-]+", sentence)]
        score = sum(token_counts[token] for token in tokens if token in token_counts)
        scores.append((score, sentence))

    ranked = [sentence for _, sentence in sorted(scores, key=lambda item: item[0], reverse=True)]
    key_points = ranked[: max_sentences + 2]
    summary = ' '.join(ranked[:max_sentences]).strip()
    return (summary or sentences[0]), key_points


def summarize_transcript(transcript: str, *, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Generate structured summary artifacts from a transcript."""
    cleaned = _clean_text(transcript)
    if not cleaned:
        return {
            'summary': 'No transcript was provided.',
            'key_points': [],
            'action_items': [],
            'keywords': [],
            'entities': [],
            'language': language,
            'confidence': 0.0,
        }

    sentences = _split_sentences(cleaned)
    summary, key_points = _summarize(sentences)
    action_items = _extract_action_items(sentences)
    keywords = _extract_keywords(cleaned)
    entities = _extract_named_entities(cleaned)

    confidence = 0.55
    if len(sentences) >= 2:
        confidence += 0.15
    if keywords:
        confidence += 0.1
    if action_items:
        confidence += 0.1
    if entities:
        confidence += 0.1

    return {
        'summary': summary,
        'key_points': key_points,
        'action_items': [item['task'] for item in action_items],
        'keywords': [item['keyword'] for item in keywords],
        'entities': entities,
        'language': language,
        'confidence': round(min(confidence, 1.0), 3),
        'details': {
            'keywords': keywords,
            'action_items': action_items,
            'sentence_count': len(sentences),
        },
    }


def analyze_transcript(transcript: str, *, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Analyze a transcript with cleaning and extraction phases."""
    artifacts = summarize_transcript(transcript, language=language)
    return {
        'transcript': transcript,
        'cleaned_transcript': _clean_text(transcript),
        'analysis': artifacts,
    }
