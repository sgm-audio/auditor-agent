# MAAPS Auditor Agent

Local DSP audio analysis and quality gatekeeper for the MAAPS (Multi-Agent Audio Production System) suite.

## Features

- **Sonic Signature Extraction**: Analyzes input audio to extract immutable acoustic fingerprints:
  - BPM (Beat tracking)
  - Musical Key (Chromagram correlation with Krumhansl-Schmiedler profiles)
  - Integrated Loudness (LUFS, ITU-R BS.1770 via `pyloudnorm`)
  - True Peak (dBTP)
  - Spectral Centroid, Spectral Rolloff, and Zero-Crossing Rate
- **Quality Gatekeeping**: Early rejection of poor input (clipping detection, high noise floor estimation, duration checks).
- **Output Critique**: Compares generated audio against expected style and loudness targets, returning structured `AuditorCritique` feedback.

## Installation

```bash
pip install maaps-auditor
```

Or install from source:

```bash
git clone https://github.com/scottmills306/auditor-agent.git
cd auditor-agent
pip install -e .
```

## Usage

### Python API

```python
import asyncio
from auditor_agent import AuditorAgent

async def main():
    agent = AuditorAgent()
    # Analyze an audio file
    signature = await agent.analyze("path/to/your/audio.wav")
    print(f"BPM: {signature.bpm}, Key: {signature.key}, Loudness: {signature.loudness_lufs} LUFS")
    
    if not signature.acceptable:
        print(f"Rejected: {signature.rejection_reason}")

if __name__ == "__main__":
    asyncio.run(main())
```

### CLI (Coming Soon)

```bash
maaps-auditor analyze track.wav --target-lufs -14.0
```

## Dependencies

- `librosa`: Audio and music analysis
- `pyloudnorm`: ITU-R BS.1770 loudness measurement
- `pydantic`: Data validation and immutable schemas

## License

MIT License. Part of the MAAPS ecosystem.
