from __future__ import annotations

import re
from collections import Counter
from typing import Any


STOPWORDS = {
	'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were',
	'you', 'your', 'they', 'them', 'their', 'about', 'into', 'will', 'shall', 'than',
	'been', 'there', 'here', 'when', 'what', 'where', 'which', 'would', 'could', 'should',
	'need', 'todo', 'also', 'while', 'over', 'under', 'after', 'before', 'more', 'most',
	'some', 'such', 'has', 'had', 'not', 'can', 'may', 'might', 'one', 'all', 'any',
	'our', 'out', 'use', 'used', 'using', 'session', 'note', 'notes',
}


def summarize_transcript(transcript: str) -> dict[str, Any]:
	cleaned = ' '.join(transcript.split())
	if not cleaned:
		return {
			'summary': 'No transcript was provided.',
			'key_points': [],
			'action_items': [],
			'keywords': [],
		}

	sentences = [segment.strip() for segment in re.split(r'(?<=[.!?])\s+|\n+', cleaned) if segment.strip()]
	summary = ' '.join(sentences[:2]) if sentences else cleaned[:240]

	key_points: list[str] = []
	for sentence in sentences[:5]:
		if len(sentence) > 30:
			key_points.append(sentence)
	if not key_points:
		key_points = sentences[:3] if sentences else [cleaned[:240]]

	action_candidates: list[str] = []
	for line in re.split(r'\n+', transcript):
		stripped = line.strip(' -•\t')
		if not stripped:
			continue
		lowered = stripped.lower()
		if any(token in lowered for token in ('action item', 'follow up', 'need to', 'should', 'must', 'todo', 'to do', 'next step', 'assign')):
			action_candidates.append(stripped)
	if not action_candidates:
		for sentence in sentences:
			lowered = sentence.lower()
			if any(token in lowered for token in ('need', 'should', 'follow up', 'next', 'action')):
				action_candidates.append(sentence)
	action_items = action_candidates[:5]

	words = [match.lower() for match in re.findall(r"[A-Za-z][A-Za-z'-]+", cleaned)]
	keywords = [word for word, _ in Counter(word for word in words if word not in STOPWORDS).most_common(8)]

	return {
		'summary': summary,
		'key_points': key_points,
		'action_items': action_items,
		'keywords': keywords,
	}


def analyze_transcript(transcript: str) -> dict[str, Any]:
	artifacts = summarize_transcript(transcript)
	return {
		'transcript': transcript,
		'analysis': artifacts,
	}
