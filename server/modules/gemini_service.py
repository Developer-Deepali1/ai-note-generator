from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Any, Mapping, TypedDict

from utils.logger import get_logger


class MeetingNotes(TypedDict):
	summary: str
	key_points: list[str]
	action_items: list[str]
	decisions: list[str]
	risks: list[str]
	follow_ups: list[str]


class GeminiServiceError(RuntimeError):
	"""Raised when Gemini note generation cannot produce a valid response."""


@dataclass(frozen=True, slots=True)
class GeminiConfig:
	"""Runtime configuration for Gemini meeting note generation."""

	api_key: str
	model_name: str
	timeout_seconds: float
	max_retries: int
	retry_initial_delay_seconds: float
	retry_max_delay_seconds: float
	temperature: float
	max_output_tokens: int

	@classmethod
	def from_env(cls) -> "GeminiConfig":
		api_key = (
			os.getenv("GEMINI_API_KEY")
			or os.getenv("GOOGLE_API_KEY")
			or os.getenv("GOOGLE_GEMINI_API_KEY")
			or ""
		).strip()
		if not api_key:
			raise GeminiServiceError(
				"Gemini API key is not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY."
			)

		model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"

		return cls(
			api_key=api_key,
			model_name=model_name,
			timeout_seconds=_read_float("GEMINI_TIMEOUT_SECONDS", 30.0, minimum=1.0),
			max_retries=_read_int("GEMINI_MAX_RETRIES", 2, minimum=0, maximum=5),
			retry_initial_delay_seconds=_read_float(
				"GEMINI_RETRY_INITIAL_DELAY_SECONDS", 0.75, minimum=0.0
			),
			retry_max_delay_seconds=_read_float("GEMINI_RETRY_MAX_DELAY_SECONDS", 5.0, minimum=0.0),
			temperature=_read_float("GEMINI_TEMPERATURE", 0.2, minimum=0.0, maximum=2.0),
			max_output_tokens=_read_int(
				"GEMINI_MAX_OUTPUT_TOKENS", 2048, minimum=128, maximum=8192
			),
		)


_LOGGER = get_logger("ai_note_generator.gemini_service")
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gemini-notes")
_EMPTY_NOTES: MeetingNotes = {
	"summary": "",
	"key_points": [],
	"action_items": [],
	"decisions": [],
	"risks": [],
	"follow_ups": [],
}


def generate_meeting_notes(transcript: str) -> MeetingNotes:
	"""Generate structured meeting notes from a transcript using Google Gemini.

	The function returns structured JSON only and falls back to an empty, validated
	payload when Gemini cannot produce a safe response.
	"""
	cleaned_transcript = _clean_transcript(transcript)
	if not cleaned_transcript:
		return dict(_EMPTY_NOTES)

	try:
		config = GeminiConfig.from_env()
	except GeminiServiceError as exc:
		_LOGGER.error("Gemini configuration error", error=str(exc))
		return dict(_EMPTY_NOTES)

	last_error: Exception | None = None
	for attempt in range(config.max_retries + 1):
		try:
			result = _generate_with_timeout(config, cleaned_transcript)
			validated = _validate_notes_payload(result)
			if validated is not None:
				return validated
			raise GeminiServiceError("Gemini returned an invalid meeting notes payload.")
		except Exception as exc:  # noqa: BLE001 - intentional production boundary
			last_error = exc
			_LOGGER.error(
				"Gemini meeting note generation failed",
				attempt=attempt + 1,
				max_retries=config.max_retries,
				error=str(exc),
			)
			if attempt < config.max_retries:
				delay = _retry_delay_seconds(
					config.retry_initial_delay_seconds,
					config.retry_max_delay_seconds,
					attempt,
				)
				if delay > 0:
					time.sleep(delay)

	if last_error is not None:
		_LOGGER.error("Gemini note generation exhausted retries", error=str(last_error))
	return dict(_EMPTY_NOTES)


def _generate_with_timeout(config: GeminiConfig, transcript: str) -> Any:
	future = _EXECUTOR.submit(_call_gemini, config, transcript)
	try:
		return future.result(timeout=config.timeout_seconds)
	except FuturesTimeoutError as exc:
		future.cancel()
		raise GeminiServiceError(
			f"Gemini request timed out after {config.timeout_seconds:.1f} seconds."
		) from exc


def _call_gemini(config: GeminiConfig, transcript: str) -> Any:
	client = _build_client(config.api_key)
	prompt = _build_prompt(transcript)
	response_text = _invoke_model(client, config.model_name, prompt, config)
	return _parse_model_output(response_text)


def _build_client(api_key: str) -> Any:
	try:
		from google import genai  # type: ignore
	except Exception:
		genai = None

	if genai is not None:
		return genai.Client(api_key=api_key)

	try:
		import google.generativeai as genai_legacy  # type: ignore
	except Exception as exc:  # pragma: no cover - dependency boundary
		raise GeminiServiceError(
			"Google Gemini SDK is not installed. Install the google-genai package."
		) from exc

	genai_legacy.configure(api_key=api_key)
	return genai_legacy


def _invoke_model(client: Any, model_name: str, prompt: str, config: GeminiConfig) -> str:
	if hasattr(client, "models"):
		response = client.models.generate_content(
			model=model_name,
			contents=prompt,
			config={
				"temperature": config.temperature,
				"max_output_tokens": config.max_output_tokens,
				"response_mime_type": "application/json",
			},
		)
		return _extract_response_text(response)

	model = client.GenerativeModel(model_name)
	response = model.generate_content(
		prompt,
		generation_config={
			"temperature": config.temperature,
			"max_output_tokens": config.max_output_tokens,
			"response_mime_type": "application/json",
		},
	)
	return _extract_response_text(response)


def _extract_response_text(response: Any) -> str:
	text = getattr(response, "text", None)
	if isinstance(text, str) and text.strip():
		return text.strip()

	parts: list[str] = []
	for candidate in _iter_response_candidates(response):
		candidate_text = getattr(candidate, "text", None)
		if isinstance(candidate_text, str) and candidate_text.strip():
			parts.append(candidate_text.strip())
	if parts:
		return "\n".join(parts).strip()

	raise GeminiServiceError("Gemini response did not contain text content.")


def _iter_response_candidates(response: Any) -> list[Any]:
	candidates: list[Any] = []
	for attr in ("candidates", "parts"):
		value = getattr(response, attr, None)
		if isinstance(value, list):
			candidates.extend(value)
	return candidates


def _parse_model_output(response_text: str) -> MeetingNotes:
	text = _strip_code_fences(response_text)
	try:
		payload = json.loads(text)
	except json.JSONDecodeError as exc:
		raise GeminiServiceError("Gemini output was not valid JSON.") from exc

	validated = _validate_notes_payload(payload)
	if validated is None:
		raise GeminiServiceError("Gemini output failed validation.")
	return validated


def _validate_notes_payload(payload: Any) -> MeetingNotes | None:
	if not isinstance(payload, Mapping):
		return None

	notes: MeetingNotes = {
		"summary": _coerce_text(payload.get("summary", "")),
		"key_points": _coerce_text_list(payload.get("key_points")),
		"action_items": _coerce_text_list(payload.get("action_items")),
		"decisions": _coerce_text_list(payload.get("decisions")),
		"risks": _coerce_text_list(payload.get("risks")),
		"follow_ups": _coerce_text_list(payload.get("follow_ups")),
	}

	if not notes["summary"] and not any(notes[key] for key in notes if key != "summary"):
		return None
	return notes


def _build_prompt(transcript: str) -> str:
	return (
		"You are a meeting notes engine. "
		"Return ONLY a valid JSON object with these exact keys: "
		'"summary", "key_points", "action_items", "decisions", "risks", "follow_ups". '
		'"summary" must be a concise plain-text paragraph. '
		'All other fields must be arrays of short plain-text strings. '
		"Do not include markdown, code fences, comments, or extra keys. "
		"Extract actionable meeting intelligence and preserve factual wording. "
		"If something is absent, return an empty array for that field.\n\n"
		f"Transcript:\n{transcript}"
	)


def _strip_code_fences(text: str) -> str:
	cleaned = text.strip()
	match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, flags=re.IGNORECASE | re.DOTALL)
	if match:
		return match.group(1).strip()
	return cleaned


def _coerce_text(value: Any) -> str:
	if value is None:
		return ""
	text = str(value).strip()
	text = text.strip("`")
	return text


def _coerce_text_list(value: Any) -> list[str]:
	if value is None:
		return []
	if isinstance(value, str):
		text = value.strip()
		return [text] if text else []
	if not isinstance(value, list):
		return []
	items: list[str] = []
	for item in value:
		text = _coerce_text(item)
		if text:
			items.append(text)
	return items


def _clean_transcript(transcript: str) -> str:
	text = str(transcript or "").replace("\r\n", "\n").replace("\r", "\n")
	text = re.sub(r"[ \t]+", " ", text)
	text = re.sub(r"\n{3,}", "\n\n", text)
	return text.strip()


def _retry_delay_seconds(initial_delay: float, max_delay: float, attempt: int) -> float:
	delay = initial_delay * (2**attempt)
	if max_delay > 0:
		delay = min(delay, max_delay)
	return max(0.0, delay)


def _read_float(name: str, default: float, *, minimum: float | None = None, maximum: float | None = None) -> float:
	value = os.getenv(name)
	if value is None or not value.strip():
		return default
	try:
		parsed = float(value)
	except ValueError:
		return default
	if minimum is not None and parsed < minimum:
		return default
	if maximum is not None and parsed > maximum:
		return default
	return parsed


def _read_int(name: str, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
	value = os.getenv(name)
	if value is None or not value.strip():
		return default
	try:
		parsed = int(value)
	except ValueError:
		return default
	if minimum is not None and parsed < minimum:
		return default
	if maximum is not None and parsed > maximum:
		return default
	return parsed


__all__ = ["GeminiServiceError", "MeetingNotes", "generate_meeting_notes"]