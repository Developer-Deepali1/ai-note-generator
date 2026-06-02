"""PDF report generation for session notes and analytics."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any


class PDFGenerationError(RuntimeError):
    """Raised when PDF generation fails."""



def _build_report_lines(session: dict[str, Any], analytics: dict[str, Any]) -> list[str]:
    notes = session.get('notes', {})
    lines = [
        'AI-Powered Smart Note Generator & Engagement Tracker',
        '=' * 56,
        f"Session: {session.get('title', 'Untitled Session')}",
        f"Generated At: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        '',
        'Executive Summary',
        '-' * 18,
        str(notes.get('summary', 'No summary available.')),
        '',
        'Key Points',
        '-' * 10,
    ]
    lines.extend(f"- {item}" for item in notes.get('key_points', []))
    lines.append('')
    lines.append('Action Items')
    lines.append('-' * 12)
    lines.extend(f"- {item}" for item in notes.get('action_items', []))
    lines.append('')
    lines.append('Engagement Analytics')
    lines.append('-' * 20)
    for key, value in analytics.items():
        lines.append(f"{key}: {value}")
    return lines



def _fallback_pdf_bytes(lines: list[str]) -> bytes:
    text = '\n'.join(lines).replace('(', '[').replace(')', ']')
    stream = (
        'BT\n'
        '/F1 10 Tf\n'
        '50 780 Td\n'
        f'({text}) Tj\n'
        'ET'
    )
    objects = [
        '1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj',
        '2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj',
        '3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources<< /Font<< /F1 4 0 R >> >> /Contents 5 0 R >>endobj',
        '4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj',
        f'5 0 obj<< /Length {len(stream.encode("latin-1", errors="replace"))} >>stream\n{stream}\nendstream endobj',
    ]

    buffer = io.BytesIO()
    buffer.write(b'%PDF-1.4\n')
    offsets = [0]
    for obj in objects:
        offsets.append(buffer.tell())
        buffer.write(obj.encode('latin-1', errors='replace'))
        buffer.write(b'\n')

    xref_offset = buffer.tell()
    buffer.write(f'xref\n0 {len(objects)+1}\n'.encode('ascii'))
    buffer.write(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        buffer.write(f'{offset:010d} 00000 n \n'.encode('ascii'))
    buffer.write(
        f'trailer<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF'.encode('ascii')
    )
    return buffer.getvalue()



def generate_pdf_report(
    session: dict[str, Any],
    analytics: dict[str, Any],
    *,
    branding: dict[str, str] | None = None,
) -> bytes:
    """Generate a PDF report.

    Returns raw PDF bytes suitable for API download responses.
    """
    lines = _build_report_lines(session, analytics)
    if branding:
        lines.insert(0, f"Brand: {branding.get('name', 'Default')} | Theme: {branding.get('theme', 'standard')}")

    try:  # pragma: no cover - optional dependency branch
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        y = 800
        for line in lines:
            pdf.drawString(40, y, line[:110])
            y -= 14
            if y <= 50:
                pdf.showPage()
                y = 800
        pdf.save()
        return buffer.getvalue()
    except Exception:
        return _fallback_pdf_bytes(lines)



def build_pdf_report_payload(
    session: dict[str, Any],
    analytics: dict[str, Any],
    *,
    branding: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a ready-to-send payload with PDF bytes and metadata."""
    pdf_bytes = generate_pdf_report(session, analytics, branding=branding)
    return {
        'filename': f"session-report-{session.get('id', 'unknown')}.pdf",
        'content_type': 'application/pdf',
        'size_bytes': len(pdf_bytes),
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'data': pdf_bytes,
    }
