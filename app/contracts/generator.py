from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from weasyprint import HTML

from app.utils.files import ensure_parent

logger = logging.getLogger(__name__)


class ContractGenerator:
    def __init__(self, template_path: Path):
        self.template_path = template_path
        loader = FileSystemLoader(str(template_path.parent))
        self.env = Environment(loader=loader, autoescape=select_autoescape(["html", "xml"]))
        self.template = self.env.get_template(template_path.name)
        self._fallback_font_registered = False
        self._font_name = "DejaVuSans"

    def render(self, context: Dict[str, Any]) -> str:
        return self.template.render(**context)

    def generate(self, output_path: Path, context: Dict[str, Any]) -> Path:
        ensure_parent(output_path)
        html_content = self.render(context)
        try:
            HTML(string=html_content, base_url=str(self.template_path.parent)).write_pdf(str(output_path))
            return output_path
        except Exception:
            logger.exception("WeasyPrint rendering failed, using fallback PDF generator")
            return self._fallback_generate(output_path, html_content)

    def _fallback_generate(self, output_path: Path, html_content: str) -> Path:
        ensure_parent(output_path)
        self._register_fallback_font()
        text_content = self._strip_html(html_content)
        pdf = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        margin = 40
        line_height = 14
        cursor_y = height - margin
        pdf.setFont(self._font_name, 11)
        for line in text_content.splitlines():
            if not line:
                cursor_y -= line_height
                continue
            wrapped = self._wrap_line(line, width - margin * 2)
            for chunk in wrapped:
                if cursor_y <= margin:
                    pdf.showPage()
                    pdf.setFont(self._font_name, 11)
                    cursor_y = height - margin
                pdf.drawString(margin, cursor_y, chunk)
                cursor_y -= line_height
        pdf.showPage()
        pdf.save()
        return output_path

    def _register_fallback_font(self) -> None:
        if self._fallback_font_registered:
            return
        font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(font_path)))
        else:
            fallback_path = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
            if fallback_path.exists():
                pdfmetrics.registerFont(TTFont("DejaVuSans", str(fallback_path)))
            else:
                self._font_name = "Helvetica"
        if self._font_name != "Helvetica":
            self._font_name = "DejaVuSans"
        self._fallback_font_registered = True

    def _strip_html(self, html_content: str) -> str:
        cleaned = re.sub(r"<\s*/p\s*>", "\n\n", html_content)
        cleaned = re.sub(r"<\s*br\s*/?>", "\n", cleaned)
        text = re.sub(r"<[^>]+>", "", cleaned)
        collapsed = re.sub(r"\s+", " ", text)
        return collapsed.replace(" .", ".").strip()

    def _wrap_line(self, line: str, max_width: float) -> List[str]:
        words = line.split(" ")
        wrapped: List[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            width = pdfmetrics.stringWidth(candidate, self._font_name, 11)
            if width <= max_width:
                current = candidate
            else:
                if current:
                    wrapped.append(current)
                current = word
        if current:
            wrapped.append(current)
        return wrapped


__all__ = ["ContractGenerator"]
