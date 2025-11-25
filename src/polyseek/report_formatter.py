"""Schema validation and Markdown rendering."""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from pydantic import BaseModel, Field, ValidationError, field_validator


class SourceModel(BaseModel):
    id: str
    title: str
    url: str = ""  # Allow empty string for sources without URLs
    type: str = Field(pattern="^(market|comment|sns|news)$")
    sentiment: str
    timestamp: str | None = None
    
    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, v):
        """Normalize URL: convert None to empty string."""
        if v is None:
            return ""
        return str(v)


class DriverModel(BaseModel):
    text: str
    source_ids: List[str] = Field(default_factory=list)


class AnalysisModel(BaseModel):
    verdict: str
    confidence_pct: float
    summary: str
    key_drivers: List[DriverModel]
    uncertainty_factors: List[str] = Field(default_factory=list)
    next_steps: List[str] | None = None
    sources: List[SourceModel]
    analysis_timestamp: str | None = None
    metadata: dict | None = None

    @field_validator("confidence_pct")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("confidence_pct must be between 0 and 100")
        return round(value, 1)

    @field_validator("sources")
    @classmethod
    def require_sources(cls, sources: List[SourceModel]) -> List[SourceModel]:
        # If no sources provided, create a fallback source
        if not sources:
            return [
                SourceModel(
                    id="SRC_FALLBACK",
                    title="Analysis based on market data",
                    url="",
                    type="market",
                    sentiment="neutral"
                )
            ]
        if len(sources) > 10:
            return sources[:10]
        return sources


def validate_analysis_payload(payload: dict) -> AnalysisModel:
    """Validate dict payload into strongly typed object."""
    try:
        return AnalysisModel.model_validate(payload)
    except ValidationError as exc:  # pragma: no cover
        raise ValueError(f"Invalid analysis payload: {exc}") from exc


def render_markdown(model: AnalysisModel) -> str:
    """Render Markdown sections from the validated model."""
    timestamp = model.analysis_timestamp or datetime.utcnow().isoformat()
    lines = [
        f"### Verdict: **{model.verdict}**",
        f"- Confidence: **{model.confidence_pct:.1f}%**",
        f"- Generated at: {timestamp}",
        "",
        "#### Summary",
        model.summary.strip(),
        "",
        "#### Key Drivers",
    ]
    if model.key_drivers:
        # Show all drivers for deep mode, up to 5 for quick mode
        max_drivers = 5 if model.metadata and model.metadata.get("mode") == "deep" else 3
        for driver in model.key_drivers[:max_drivers]:
            refs = ", ".join(driver.source_ids) if driver.source_ids else "n/a"
            lines.append(f"- {driver.text} _(sources: {refs})_")
    else:
        lines.append("- No salient drivers found.")

    lines.extend(["", "#### Risks / Uncertainty"])
    if model.uncertainty_factors:
        for item in model.uncertainty_factors:
            lines.append(f"- {item}")
    else:
        lines.append("- Uncertainty not specified.")

    if model.next_steps:
        lines.extend(["", "#### Next Steps"])
        for step in model.next_steps:
            lines.append(f"- {step}")

    lines.extend(["", "#### Sources"])
    grouped: dict[str, List[SourceModel]] = {"market": [], "comment": [], "sns": [], "news": []}
    for source in model.sources:
        grouped.setdefault(source.type, []).append(source)
    for group, entries in grouped.items():
        if not entries:
            continue
        lines.append(f"- **{group.upper()}**")
        for entry in entries:
            lines.append(f"  - [{entry.title}]({entry.url}) ({entry.sentiment})")

    return "\n".join(lines)


def format_response(payload: dict) -> Tuple[AnalysisModel, str]:
    """Return validated model and Markdown string."""
    model = validate_analysis_payload(payload)
    markdown = render_markdown(model)
    return model, markdown

