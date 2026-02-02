"""Import-safe CUI inspection engine.
(Uses a safe fallback implementation if the legacy upload had syntax/indentation issues.)
"""
from __future__ import annotations
import re, json
from typing import Any, Dict
try:
    import PyPDF2
except Exception:
    PyPDF2 = None
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    letter = None
    canvas = None

class CUIInspector:
    """Safe, minimal CUI inspector (fallback if legacy extraction is broken)."""
    def __init__(self):
        self.patterns = {
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
            "DoD_ID": r"\b\d{10}\b",
            "Email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "CAGE": r"\b[A-HJ-NP-Z0-9]{5}\b",
        }

    def inspect_text(self, text: str, name: str = "text"):
        found = {}
        for k, pat in self.patterns.items():
            m = re.findall(pat, text or "")
            if m:
                found[k] = len(m)
        risk = "LOW"
        if found:
            risk = "MEDIUM"
        if sum(found.values()) >= 10:
            risk = "HIGH"
        return {
            "filename": name,
            "cui_detected": bool(found),
            "risk_level": risk,
            "patterns_found": found,
            "cui_categories": list(found.keys()),
        }

    def inspect_file(self, filename: str, data: bytes):
        text = self.extract_text_from_file(filename, data)
        return self.inspect_text(text, filename)

    def extract_text_from_file(self, filename: str, data: bytes) -> str:
        # basic: decode; if PDF and PyPDF2 is available try extract
        fn = (filename or "").lower()
        if fn.endswith(".pdf") and PyPDF2 is not None:
            try:
                import io
                reader = PyPDF2.PdfReader(io.BytesIO(data))
                return "\n".join([p.extract_text() or "" for p in reader.pages])
            except Exception:
                pass
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def generate_cui_report_pdf(self, findings: dict) -> bytes:
        # prefer reportlab if available
        if canvas is not None and letter is not None:
            import io
            buff = io.BytesIO()
            c = canvas.Canvas(buff, pagesize=letter)
            c.setFont("Helvetica", 12)
            y = 760
            c.drawString(72, y, "CUI Inspection Report")
            y -= 24
            c.drawString(72, y, f"File: {findings.get('filename')}")
            y -= 18
            c.drawString(72, y, f"Risk: {findings.get('risk_level')}")
            y -= 18
            c.drawString(72, y, f"CUI Detected: {findings.get('cui_detected')}")
            y -= 24
            c.drawString(72, y, "Patterns:")
            y -= 18
            for k, v in (findings.get("patterns_found") or {}).items():
                c.drawString(90, y, f"- {k}: {v}")
                y -= 16
                if y < 72:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 760
            c.showPage()
            c.save()
            return buff.getvalue()
        # minimal fallback bytes
        return (json.dumps(findings, indent=2)).encode("utf-8")
