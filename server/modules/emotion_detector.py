"""Emotion and sentiment analysis utilities for transcript content."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

_POSITIVE_WORDS = {
    'great', 'good', 'excellent', 'happy', 'clear', 'productive', 'awesome', 'love', 'win', 'success'
}
_NEGATIVE_WORDS = {
    'bad', 'confused', 'sad', 'frustrated', 'angry', 'blocked', 'issue', 'problem', 'stuck', 'failed'
}
_EMOTION_LEXICON: dict[str, set[str]] = {
    'joy': {'happy', 'excited', 'great', 'awesome', 'love', 'glad'},
    'confidence': {'confident', 'clear', 'ready', 'sure', 'can'},
    'concern': {'risk', 'problem', 'issue', 'worry', 'concern'},
    'frustration': {'blocked', 'stuck', 'frustrated', 'angry', 'delayed'},
    'neutral': set(),
}


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'-]+", text or '')]


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Compute sentiment score and label for text."""
    tokens = _tokenize(text)
    if not tokens:
        return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}

    positive_hits = sum(1 for token in tokens if token in _POSITIVE_WORDS)
    negative_hits = sum(1 for token in tokens if token in _NEGATIVE_WORDS)
    polarity = positive_hits - negative_hits
    normalized = polarity / max(1, len(tokens))

    if normalized > 0.03:
        label = 'positive'
    elif normalized < -0.03:
        label = 'negative'
    else:
        label = 'neutral'

    intensity = min(1.0, abs(normalized) * 4)
    confidence = min(1.0, 0.45 + (positive_hits + negative_hits) / max(1, len(tokens)))
    return {
        'label': label,
        'score': round(normalized, 4),
        'intensity': round(intensity, 3),
        'confidence': round(confidence, 3),
    }


def classify_emotions(text: str) -> dict[str, Any]:
    """Classify dominant emotion and scores from text."""
    tokens = _tokenize(text)
    if not tokens:
        return {'dominant_emotion': 'neutral', 'emotion_scores': {'neutral': 0.0}, 'intensity': 0.0}

    counts = Counter()
    for token in tokens:
        for emotion, lexicon in _EMOTION_LEXICON.items():
            if token in lexicon:
                counts[emotion] += 1

    if not counts:
        counts['neutral'] = 1

    total = sum(counts.values())
    emotion_scores = {emotion: round(value / total, 3) for emotion, value in counts.items()}
    dominant_emotion = max(emotion_scores, key=emotion_scores.get)
    return {
        'dominant_emotion': dominant_emotion,
        'emotion_scores': emotion_scores,
        'intensity': round(min(1.0, emotion_scores.get(dominant_emotion, 0.0) + 0.1), 3),
    }


def sentence_level_emotions(transcript: str) -> list[dict[str, Any]]:
    """Analyze emotions per sentence in temporal order."""
    sentences = [segment.strip() for segment in re.split(r'(?<=[.!?])\s+|\n+', transcript or '') if segment.strip()]
    timeline: list[dict[str, Any]] = []
    for index, sentence in enumerate(sentences):
        sentiment = analyze_sentiment(sentence)
        emotion = classify_emotions(sentence)
        timeline.append(
            {
                'index': index,
                'sentence': sentence,
                'sentiment': sentiment['label'],
                'emotion': emotion['dominant_emotion'],
                'intensity': max(sentiment['intensity'], emotion['intensity']),
            }
        )
    return timeline


def speaker_level_emotions(transcript: str) -> dict[str, dict[str, Any]]:
    """Group emotional profile by `Speaker: utterance` patterns."""
    profile: dict[str, list[str]] = {}
    for line in transcript.splitlines():
        match = re.match(r'^([A-Za-z][A-Za-z0-9_\- ]{0,60}):\s*(.+)$', line.strip())
        if not match:
            continue
        speaker = match.group(1).strip()
        utterance = match.group(2).strip()
        profile.setdefault(speaker, []).append(utterance)

    return {
        speaker: {
            'sentiment': analyze_sentiment(' '.join(lines)),
            'emotion': classify_emotions(' '.join(lines)),
            'utterance_count': len(lines),
        }
        for speaker, lines in profile.items()
    }


def detect_emotions(transcript: str, *, engagement_score: float | None = None) -> dict[str, Any]:
    """Run multi-level emotion analysis and correlate with engagement."""
    sentiment = analyze_sentiment(transcript)
    emotion = classify_emotions(transcript)
    sentence_timeline = sentence_level_emotions(transcript)
    speaker_timeline = speaker_level_emotions(transcript)

    correlation = None
    if engagement_score is not None:
        correlation = round((emotion['intensity'] + (engagement_score if engagement_score <= 1 else engagement_score / 100)) / 2, 3)

    return {
        'sentiment': sentiment,
        'emotion': emotion,
        'sentence_timeline': sentence_timeline,
        'speaker_analysis': speaker_timeline,
        'engagement_correlation': correlation,
    }
