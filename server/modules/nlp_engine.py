from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'but', 'by', 'can', 'could',
    'did', 'do', 'does', 'for', 'from', 'had', 'has', 'have', 'here', 'if', 'in',
    'into', 'is', 'it', 'its', 'may', 'might', 'more', 'most', 'need', 'not', 'of',
    'on', 'or', 'our', 'out', 'over', 'shall', 'should', 'some', 'such', 'than',
    'that', 'the', 'their', 'them', 'there', 'they', 'this', 'to', 'todo', 'under',
    'use', 'used', 'using', 'was', 'were', 'what', 'when', 'where', 'which', 'while',
    'will', 'with', 'would', 'you', 'your', 'session', 'note', 'notes', 'meeting',
}

ACTION_PATTERNS = (
    r'\baction\s+item\b',
    r'\bfollow\s+up\b',
    r'\bnext\s+step\b',
    r'\bto\s+do\b',
    r'\btodo\b',
    r'\bneed(?:s|ed)?\s+to\b',
    r'\bmust\b',
    r'\bshould\b',
    r'\bassign(?:ed|ment)?\b',
    r'\bowner\b',
)

DATE_PATTERN = re.compile(
    r'\b(?:today|tomorrow|this\s+week|next\s+week|'
    r'monday|tuesday|wednesday|thursday|friday|saturday|sunday|'
    r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
    r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|'
    r'\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b',
    re.IGNORECASE,
)

SPEAKER_PATTERN = re.compile(r'^\s*([A-Z][A-Za-z ._-]{1,60}):\s+(.+)$')
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
ACRONYM_PATTERN = re.compile(r'\b[A-Z]{2,}(?:-[A-Z0-9]+)?\b')
PROPER_NOUN_PATTERN = re.compile(r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b')


@dataclass(frozen=True)
class Sentence:
    text: str
    index: int
    speaker: str | None = None


def clean_transcript(transcript: str) -> str:
    text = str(transcript or '').replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def segment_sentences(transcript: str) -> list[Sentence]:
    cleaned = clean_transcript(transcript)
    if not cleaned:
        return []

    sentences: list[Sentence] = []
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        speaker: str | None = None
        content = line
        speaker_match = SPEAKER_PATTERN.match(line)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            content = speaker_match.group(2).strip()

        parts = re.split(r'(?<=[.!?])\s+', content)
        for part in parts:
            text = part.strip(' -\t')
            if text:
                prefix = f'{speaker}: ' if speaker else ''
                sentences.append(Sentence(f'{prefix}{text}', len(sentences), speaker))

    return sentences


def _tokenize(text: str) -> list[str]:
    return [word.lower().strip("'") for word in WORD_PATTERN.findall(text)]


def _keyword_counts(text: str) -> Counter[str]:
    tokens = [
        token
        for token in _tokenize(text)
        if len(token) > 2 and token not in STOPWORDS and not token.isnumeric()
    ]
    counts: Counter[str] = Counter(tokens)

    lower = text.lower()
    for phrase in re.findall(r'\b[a-z][a-z0-9-]+(?:\s+[a-z][a-z0-9-]+){1,3}\b', lower):
        words = phrase.split()
        if any(word in STOPWORDS for word in words):
            continue
        if len(' '.join(words)) <= 80:
            counts[phrase] += len(words)

    return counts


def extract_keywords(transcript: str, limit: int = 10) -> list[str]:
    counts = _keyword_counts(transcript)
    return [word for word, _ in counts.most_common(limit)]


def _score_sentence(sentence: Sentence, keywords: Counter[str], total_sentences: int) -> float:
    tokens = _tokenize(sentence.text)
    meaningful = [token for token in tokens if token not in STOPWORDS]
    if not meaningful:
        return 0.0

    keyword_score = sum(keywords.get(token, 0) for token in meaningful) / len(meaningful)
    action_boost = 1.3 if _looks_like_action(sentence.text) else 1.0
    position_boost = 1.15 if sentence.index in {0, total_sentences - 1} else 1.0
    length_penalty = 0.75 if len(tokens) < 6 or len(tokens) > 45 else 1.0
    return keyword_score * action_boost * position_boost * length_penalty


def extract_key_points(transcript: str, limit: int = 5) -> list[str]:
    sentences = segment_sentences(transcript)
    if not sentences:
        return []

    keyword_counts = _keyword_counts(transcript)
    ranked = sorted(
        sentences,
        key=lambda sentence: (-_score_sentence(sentence, keyword_counts, len(sentences)), sentence.index),
    )

    selected: list[Sentence] = []
    seen_normalized: set[str] = set()
    for sentence in ranked:
        normalized = re.sub(r'\W+', '', sentence.text.casefold())
        if len(sentence.text) < 20 or normalized in seen_normalized:
            continue
        seen_normalized.add(normalized)
        selected.append(sentence)
        if len(selected) >= limit:
            break

    if not selected:
        selected = sentences[:limit]

    return [sentence.text for sentence in sorted(selected, key=lambda item: item.index)]


def _looks_like_action(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in ACTION_PATTERNS)


def _extract_owner(text: str, speaker: str | None) -> str | None:
    assignment = re.search(
        r'\b(?:assign(?:ed)?\s+to|owner\s*:|owner\s+is|by)\s+([A-Z][A-Za-z ._-]{1,40})',
        text,
    )
    if assignment:
        return assignment.group(1).strip(' .')

    leading_name = re.match(r'^([A-Z][A-Za-z ._-]{1,40})\s+(?:will|should|must|to)\b', text)
    if leading_name:
        return leading_name.group(1).strip(' .')

    return speaker


def extract_action_items(transcript: str, limit: int = 8) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()

    for sentence in segment_sentences(transcript):
        if not _looks_like_action(sentence.text):
            continue

        item = re.sub(r'^\s*(?:action\s+item|todo|to\s+do|next\s+step)\s*[:\-]\s*', '', sentence.text, flags=re.I)
        owner = _extract_owner(item, sentence.speaker)
        due_match = DATE_PATTERN.search(item)

        details: list[str] = []
        if owner:
            details.append(f'Owner: {owner}')
        if due_match:
            details.append(f'Due: {due_match.group(0)}')

        formatted = item.strip()
        if details:
            formatted = f'{formatted} ({", ".join(details)})'

        normalized = formatted.casefold()
        if normalized not in seen:
            seen.add(normalized)
            actions.append(formatted)
        if len(actions) >= limit:
            break

    return actions


def extract_named_entities(transcript: str, limit: int = 20) -> list[dict[str, str]]:
    cleaned = clean_transcript(transcript)
    if not cleaned:
        return []

    entities: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for acronym in ACRONYM_PATTERN.findall(cleaned):
        key = (acronym, 'ORG')
        if key not in seen:
            seen.add(key)
            entities.append({'text': acronym, 'type': 'ORG'})

    for match in PROPER_NOUN_PATTERN.findall(cleaned):
        text = match.strip()
        if text.lower() in {'action item', 'next step'}:
            continue
        entity_type = 'PERSON' if len(text.split()) <= 2 else 'OTHER'
        key = (text, entity_type)
        if key not in seen:
            seen.add(key)
            entities.append({'text': text, 'type': entity_type})

    for date in DATE_PATTERN.findall(cleaned):
        text = str(date).strip()
        key = (text, 'DATE')
        if key not in seen:
            seen.add(key)
            entities.append({'text': text, 'type': 'DATE'})

    return entities[:limit]


def summarize_transcript(transcript: str) -> dict[str, Any]:
    cleaned = clean_transcript(transcript)
    if not cleaned:
        return {
            'summary': 'No transcript was provided.',
            'key_points': [],
            'action_items': [],
            'keywords': [],
            'entities': [],
            'metadata': {
                'word_count': 0,
                'sentence_count': 0,
                'speaker_count': 0,
                'estimated_reading_minutes': 0,
            },
        }

    sentences = segment_sentences(cleaned)
    key_points = extract_key_points(cleaned)
    summary_sentences = key_points[:2] if key_points else [sentence.text for sentence in sentences[:2]]
    summary = ' '.join(summary_sentences).strip()
    if not summary:
        summary = cleaned[:240]

    words = _tokenize(cleaned)
    speakers = {sentence.speaker for sentence in sentences if sentence.speaker}

    return {
        'summary': summary,
        'key_points': key_points,
        'action_items': extract_action_items(cleaned),
        'keywords': extract_keywords(cleaned),
        'entities': extract_named_entities(cleaned),
        'metadata': {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'speaker_count': len(speakers),
            'estimated_reading_minutes': max(1, round(len(words) / 180)) if words else 0,
        },
    }


def classify_transcript(transcript: str) -> dict[str, Any]:
    lowered = clean_transcript(transcript).lower()
    domain_terms = {
        'planning': {'roadmap', 'milestone', 'deadline', 'timeline', 'resources', 'priority'},
        'education': {'class', 'lesson', 'assignment', 'student', 'teacher', 'exam'},
        'standup': {'yesterday', 'today', 'blocked', 'blocker', 'sprint', 'ticket'},
        'sales': {'client', 'deal', 'proposal', 'contract', 'pricing', 'renewal'},
        'support': {'issue', 'bug', 'incident', 'customer', 'ticket', 'resolution'},
    }
    scores = {
        label: sum(1 for term in terms if re.search(rf'\b{re.escape(term)}\b', lowered))
        for label, terms in domain_terms.items()
    }
    category = max(scores, key=scores.get) if any(scores.values()) else 'general'
    return {'category': category, 'scores': scores}


def analyze_transcript(transcript: str) -> dict[str, Any]:
    artifacts = summarize_transcript(transcript)
    return {
        'transcript': clean_transcript(transcript),
        'analysis': artifacts,
        'classification': classify_transcript(transcript),
    }
