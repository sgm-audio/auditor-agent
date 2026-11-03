"""Schema validation tests (no audio dependencies)."""

import pytest
from pydantic import ValidationError

from auditor_agent.schemas import AuditorCritique, SonicSignature


def make_signature(**overrides):
    data = dict(
        bpm=120.0,
        key="C minor",
        loudness_lufs=-14.0,
        true_peak_dbtp=-1.0,
        spectral_centroid_hz=1000.0,
        spectral_rolloff_hz=5000.0,
        zero_crossing_rate=0.05,
        duration_seconds=3.2,
    )
    data.update(overrides)
    return SonicSignature(**data)


def test_sonic_signature_valid():
    sig = make_signature()
    assert sig.key == "C minor"
    assert sig.sample_rate == 44100
    assert sig.channels == 2
    assert sig.acceptable is True


def test_sonic_signature_is_frozen():
    sig = make_signature()
    with pytest.raises(ValidationError):
        sig.bpm = 100.0  # type: ignore[misc]


def test_sonic_signature_rejects_bad_key():
    with pytest.raises(ValidationError):
        make_signature(key="H# major")


def test_sonic_signature_rejects_out_of_range_bpm():
    with pytest.raises(ValidationError):
        make_signature(bpm=400.0)


def test_key_normalisation():
    sig = make_signature(key="c#min")
    assert sig.key == "C# minor"


def test_auditor_critique_defaults():
    critique = AuditorCritique(approved=False, rejection_reasons=["too quiet"])
    assert critique.approved is False
    assert critique.rejection_reasons == ["too quiet"]
    assert critique.clipping is False
    assert critique.telemetry == {}
