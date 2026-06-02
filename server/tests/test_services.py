from __future__ import annotations

from modules.analytics_engine import calculate_analytics_summary, export_analytics_data
from modules.emotion_detector import detect_emotions
from modules.pdf_generator import build_pdf_report_payload
from modules.speech_to_text import transcribe_payload
from utils.decorators import validate_request
from utils.file_handler import sanitize_filename



def test_transcribe_payload_supports_partial_chunks():
    result = transcribe_payload({'partial_transcripts': ['Hello', 'world']})
    assert result['is_partial'] is True
    assert result['transcript'] == 'Hello world'



def test_pdf_payload_is_generated():
    payload = build_pdf_report_payload(
        {'id': '1', 'title': 'Weekly', 'notes': {'summary': 'Summary', 'key_points': [], 'action_items': []}},
        {'engagement_average': 85.0},
    )
    assert payload['content_type'] == 'application/pdf'
    assert payload['size_bytes'] > 0



def test_analytics_summary_and_export_json():
    summary = calculate_analytics_summary(
        attendance_total=10,
        attendance_present=8,
        engagement_scores=[70, 75, 80],
        participation_events=[{'event_type': 'spoke'}, {'event_type': 'focus'}],
    )
    rendered = export_analytics_data(summary)
    assert summary['attendance_percentage'] == 80.0
    assert 'attendance_percentage' in rendered



def test_emotion_detector_returns_timeline():
    result = detect_emotions('Alice: Great progress. Bob: We are blocked by one issue.')
    assert 'sentence_timeline' in result



def test_file_handler_sanitizes_name():
    assert sanitize_filename('../unsafe name.mp3') == 'unsafe_name.mp3'



def test_validate_request_decorator():
    @validate_request(required_fields=('session_id',))
    def process(payload: dict[str, str]) -> str:
        return payload['session_id']

    assert process({'session_id': 'abc'}) == 'abc'
