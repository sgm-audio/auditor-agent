"""
MAAPS Auditor Agent - Strict Pydantic Schemas
Immutable sonic signatures and critique outputs for audio analysis.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re

class SonicSignature(BaseModel):
    """Immutable sonic fingerprint from Auditor Agent"""
    model_config = ConfigDict(frozen=True)

    # Core metrics
    bpm: float = Field(ge=40.0, le=220.0, description="Beats per minute")
    key: str = Field(pattern=r"^[A-G][#b]?\s?(major|minor)$", description="Musical key e.g., 'C major'")
    loudness_lufs: float = Field(ge=-70.0, le=0.0, description="Integrated loudness LUFS")
    true_peak_dbtp: float = Field(ge=-70.0, le=10.0, description="True peak dBTP")

    # Spectral features
    spectral_centroid_hz: float = Field(ge=0.0, description="Spectral centroid in Hz")
    spectral_rolloff_hz: float = Field(ge=0.0, description="Spectral rolloff frequency")
    zero_crossing_rate: float = Field(ge=0.0, le=1.0, description="Zero crossing rate")

    # Quality flags
    acceptable: bool = True
    rejection_reason: Optional[str] = None
    clipping_detected: bool = False
    noise_floor_db: float = Field(default=-60.0, ge=-100.0, le=0.0)

    # Metadata
    duration_seconds: float = Field(ge=0.0)
    sample_rate: int = Field(default=44100, ge=8000, le=192000)
    bit_depth: int = Field(default=24, ge=16, le=32)
    channels: int = Field(default=2, ge=1, le=8)

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        v_lower = v.lower().replace(" ", "")
        if v_lower.endswith("maj"):
            v_lower = v_lower[:-3] + "major"
        elif v_lower.endswith("min"):
            v_lower = v_lower[:-3] + "minor"
        if not re.match(r"^[a-g][#b]?(major|minor)$", v_lower):
            raise ValueError(f"Invalid key format: {v}. Use 'C major', 'C#minor', etc.")
        match = re.match(r"^([a-g][#b]?)(major|minor)$", v_lower)
        if match:
            return f"{match.group(1).capitalize()} {match.group(2)}"
        return v

class AuditorCritique(BaseModel):
    """Auditor feedback on generated output"""
    approved: bool
    rejection_reasons: list[str] = Field(default_factory=list)
    loudness_match: bool = True
    style_match: bool = True
    technical_quality: bool = True
    too_quiet: bool = False
    too_loud: bool = False
    wrong_style: bool = False
    clipping: bool = False
    artifacts: bool = False
    telemetry: dict = Field(default_factory=dict)
