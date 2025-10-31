from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.config import Settings
from app.database import models
from app.utils.files import ensure_parent


def _build_environment(template_path: Path) -> Environment:
    loader = FileSystemLoader(str(template_path.parent))
    return Environment(loader=loader, autoescape=select_autoescape(["html", "xml"]))


@dataclass(slots=True)
class ContractContext:
    release: models.Release
    consent: models.Consent
    payment: models.Payment


class ContractService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.env = _build_environment(settings.contract_template)
        self.template = self.env.get_template(settings.contract_template.name)

    def render(self, context: ContractContext) -> Path:
        output_path = self.settings.contracts_dir / f"contract_release_{context.release.id}.pdf"
        ensure_parent(output_path)
        html_content = self.template.render(
            release=context.release,
            consent=context.consent,
            payment=context.payment,
            generated_at=datetime.utcnow(),
        )
        HTML(string=html_content).write_pdf(str(output_path))
        return output_path


__all__ = ["ContractService", "ContractContext"]
