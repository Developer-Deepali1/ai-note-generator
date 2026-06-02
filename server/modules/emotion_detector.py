from __future__ import annotations

import re
from typing import Any

from utils.constants import EMOTION_SCORES


EMOTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    'focused': ('focused', 'clear', 'aligned', 'understood', 'concentrating'),
    'engaged': ('great question', 'discuss', 'collaborate', 'interested', 'agree'),
    'happy': ('happy', 'excited', 'great', 'excellent', 'pleased'),
    'neutral': ('okay', 'noted', 'fine', 'understood'),
    'confused': ('confused', 'unclear', 'lost', 'question', 'clarify'),
    'distracted': ('distracted', 'away', 'missed', 'repeat', 'background'),
    'frustrated': ('frustrated', 'blocked', 'stuck', 'annoyed', 'problem'),
    'sad': ('sad', 'disappointed', 'concerned', 'unhappy'),
}


def detect_emotion(text: str = '', signals: dict[str, Any] | None = None) -> dict[str, Any]:
    signal_payload = signals or {}
    explicit = str(signal_payload.get('emotion') or signal_payload.get('sentiment') or '').lower().strip()
    if explicit in EMOTION_SCORES:
        return {'emotion': explicit, 'score': EMOTION_SCORES[explicit], 'source': 'explicit'}

    lowered = str(text or '').lower()
    matches = {
        emotion: sum(1 for keyword in keywords if re.search(rf'\b{re.escape(keyword)}\b', lowered))
        for emotion, keywords in EMOTION_KEYWORDS.items()
    }
    emotion = max(matches, key=matches.get) if any(matches.values()) else 'neutral'
    return {
        'emotion': emotion,
        'score': EMOTION_SCORES.get(emotion, 0.65),
        'source': 'text' if any(matches.values()) else 'default',
        'matches': matches,
    }
