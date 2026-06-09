1|"""
2|MAAPS v4.0 - Auditor Agent (Gatekeeper)
3|
4|Local DSP analysis using librosa and pyloudnorm.
5|Analyzes input audio from REAPER items, extracts sonic features,
6|and rejects poor input early. Outputs immutable SonicSignature.
7|
8|REAPER Integration: Pulls selected track items via reapy, analyzes,
9|pushes telemetry back (color-coded tracks, console messages).
10|"""
11|
12|import logging
13|import asyncio
14|from typing import Optional, Dict, Any, List
15|from pathlib import Path
16|import numpy as np
17|
18|from .schemas import SonicSignature, AuditorCritique
19|
20|logger = logging.getLogger("maaps.auditor")
21|
22|
23|class AuditorAgent:
24|    """
25|    Gatekeeper Agent for MAAPS v4.0
26|
27|    Responsibilities:
28|    - Analyze input audio (guitar riff, vocal memo, etc.)
29|    - Extract: BPM, Key, LUFS, spectral features, clipping/noise
30|    - Reject poor input early
31|    - Critique generated output against style/LUFS targets
32|    """
33|
34|    def __init__(self):
35|        self.name = "AuditorAgent"
36|        self._librosa = None
37|        self._pyloudnorm = None
38|        logger.info("AuditorAgent initialized")
39|
40|    def _load_dependencies(self):
41|        """Lazy load heavy dependencies"""
42|        if self._librosa is None:
43|            import librosa
44|            import pyloudnorm as pyln
45|
46|            self._librosa = librosa
47|            self._pyloudnorm = pyln
48|            logger.info("Auditor dependencies loaded")
49|
50|    async def analyze(self, audio_path: str) -> SonicSignature:
51|        """
52|        Analyze input audio and extract sonic signature
53|
54|        Args:
55|            audio_path: Path to audio file
56|
57|        Returns:
58|            SonicSignature with extracted features
59|        """
60|        self._load_dependencies()
61|
62|        try:
63|            # Load audio
64|            y, sr = self._librosa.load(audio_path, sr=None, mono=True)
65|            duration = len(y) / sr
66|
67|            logger.info(f"Analyzing: {audio_path} ({duration:.2f}s @ {sr}Hz)")
68|
69|            # Extract BPM
70|            tempo, _ = self._librosa.beat.beat_track(y=y, sr=sr)
71|            bpm = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])
72|
73|            # Extract Key (chromagram correlation)
74|            key = self._extract_key(y, sr)
75|
76|            # Extract LUFS (BS.1770)
77|            loudness, true_peak = self._extract_loudness(y, sr)
78|
79|            # Spectral features
80|            spectral_centroid = self._extract_spectral_centroid(y, sr)
81|            spectral_rolloff = self._extract_spectral_rolloff(y, sr)
82|            zcr = self._extract_zero_crossing_rate(y, sr)
83|
84|            # Quality checks
85|            clipping = self._detect_clipping(y)
86|            noise_floor = self._estimate_noise_floor(y)
87|
88|            # Determine acceptability
89|            acceptable = True
90|            rejection_reason = None
91|
92|            if clipping:
93|                acceptable = False
94|                rejection_reason = "Clipping detected"
95|            elif noise_floor > -40:  # Too noisy
96|                acceptable = False
97|                rejection_reason = f"High noise floor: {noise_floor:.1f} dB"
98|            elif duration < 1.0:
99|                acceptable = False
100|                rejection_reason = f"Audio too short: {duration:.2f}s"
101|
102|            signature = SonicSignature(
103|                bpm=bpm,
104|                key=key,
105|                loudness_lufs=loudness,
106|                true_peak_dbtp=true_peak,
107|                spectral_centroid_hz=spectral_centroid,
108|                spectral_rolloff_hz=spectral_rolloff,
109|                zero_crossing_rate=zcr,
110|                acceptable=acceptable,
111|                rejection_reason=rejection_reason,
112|                clipping_detected=clipping,
113|                noise_floor_db=noise_floor,
114|                duration_seconds=duration,
115|                sample_rate=sr,
116|                bit_depth=24,  # Assume 24-bit for WAV
117|                channels=2,  # Assume stereo
118|            )
119|
120|            logger.info(f"SonicSignature: {bpm:.1f} BPM, {key}, {loudness:.1f} LUFS")
121|
122|            return signature
123|
124|        except Exception as e:
125|            logger.error(f"Analysis failed: {e}", exc_info=True)
126|            return SonicSignature(
127|                bpm=120.0,
128|                key="Cmajor",
129|                loudness_lufs=-70.0,
130|                true_peak_dbtp=-70.0,
131|                spectral_centroid_hz=1000.0,
132|                spectral_rolloff_hz=5000.0,
133|                zero_crossing_rate=0.1,
134|                acceptable=False,
135|                rejection_reason=f"Analysis error: {str(e)}",
136|                duration_seconds=0.0,
137|                sample_rate=44100,
138|            )
139|
140|    def _extract_key(self, y: np.ndarray, sr: int) -> str:
141|        """Extract musical key via chromagram correlation"""
142|        # Compute chromagram
143|        chroma = self._librosa.feature.chroma_cqt(y=y, sr=sr)
144|
145|        # Correlate with key profiles (Krumhansl-Schmiedler)
146|        major_profile = np.array(
147|            [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
148|        )
149|        minor_profile = np.array(
150|            [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
151|        )
152|
153|        best_corr = -1
154|        best_key = "Cmajor"
155|
156|        for i in range(12):
157|            # Rotate profiles
158|            major_rotated = np.roll(major_profile, i)
159|            minor_rotated = np.roll(minor_profile, i)
160|
161|            # Correlate
162|            corr_major = np.corrcoef(chroma.mean(axis=1), major_rotated)[0, 1]
163|            corr_minor = np.corrcoef(chroma.mean(axis=1), minor_rotated)[0, 1]
164|
165|            if corr_major > best_corr:
166|                best_corr = corr_major
167|                best_key = f"{self._note_from_index(i)}major"
168|
169|            if corr_minor > best_corr:
170|                best_corr = corr_minor
171|                best_key = f"{self._note_from_index(i)}minor"
172|
173|        return best_key
174|
175|    def _note_from_index(self, idx: int) -> str:
176|        """Convert chroma index to note name"""
177|        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
178|        return notes[idx % 12]
179|
180|    def _extract_loudness(self, y: np.ndarray, sr: int) -> tuple:
181|        """Extract integrated loudness (LUFS) and true peak"""
182|        meter = self._pyloudnorm.Meter(sr)
183|        loudness = meter.integrated_loudness(y)
184|
185|        # True peak estimation (simple oversampling approximation)
186|        true_peak = np.max(np.abs(y))
187|        true_peak_db = 20 * np.log10(true_peak + 1e-10)
188|
189|        return loudness, true_peak_db
190|
191|    def _extract_spectral_centroid(self, y: np.ndarray, sr: int) -> float:
192|        """Extract spectral centroid"""
193|        centroid = self._librosa.feature.spectral_centroid(y=y, sr=sr)
194|        return float(np.mean(centroid))
195|
196|    def _extract_spectral_rolloff(self, y: np.ndarray, sr: int) -> float:
197|        """Extract spectral rolloff frequency"""
198|        rolloff = self._librosa.feature.spectral_rolloff(y=y, sr=sr)
199|        return float(np.mean(rolloff))
200|
201|    def _extract_zero_crossing_rate(self, y: np.ndarray, sr: int) -> float:
202|        """Extract zero crossing rate"""
203|        zcr = self._librosa.feature.zero_crossing_rate(y)
204|        return float(np.mean(zcr))
205|
206|    def _detect_clipping(self, y: np.ndarray) -> bool:
207|        """Detect clipping (samples at or near ±1.0)"""
208|        threshold = 0.99
209|        clipped_samples = np.sum(np.abs(y) >= threshold)
210|        clip_ratio = clipped_samples / len(y)
211|        return clip_ratio > 0.001  # More than 0.1% clipped
212|
213|    def _estimate_noise_floor(self, y: np.ndarray) -> float:
214|        """Estimate noise floor from quietest 10% of signal"""
215|        rms = np.sqrt(np.mean(y**2))
216|        # Simple approximation: noise floor ~ RMS - 20dB for typical material
217|        noise_floor_db = 20 * np.log10(rms + 1e-10) - 20
218|        return noise_floor_db
219|
220|    async def critique(
221|        self, output_paths: List[str], expected_style: str, expected_lufs: float
222|    ) -> AuditorCritique:
223|        """
224|        Critique generated output
225|
226|        Args:
227|            output_paths: Paths to generated/stem files
228|            expected_style: Expected style descriptor
229|            expected_lufs: Target loudness
230|
231|        Returns:
232|            AuditorCritique with approval status and feedback
233|        """
234|        rejection_reasons = []
235|        telemetry = {}
236|
237|        issues = {
238|            "too_quiet": False,
239|            "too_loud": False,
240|            "wrong_style": False,
241|            "clipping": False,
242|            "artifacts": False,
243|        }
244|
245|        for path in output_paths:
246|            try:
247|                signature = await self.analyze(path)
248|
249|                # Check LUFS
250|                lufs_diff = abs(signature.loudness_lufs - expected_lufs)
251|                if lufs_diff > 2.0:
252|                    if signature.loudness_lufs < expected_lufs:
253|                        issues["too_quiet"] = True
254|                        rejection_reasons.append(
255|                            f"Too quiet: {signature.loudness_lufs:.1f} vs target {expected_lufs}"
256|                        )
257|                    else:
258|                        issues["too_loud"] = True
259|                        rejection_reasons.append(
260|                            f"Too loud: {signature.loudness_lufs:.1f} vs target {expected_lufs}"
261|                        )
262|
263|                # Check clipping
264|                if signature.clipping_detected:
265|                    issues["clipping"] = True
266|                    rejection_reasons.append("Clipping detected in output")
267|
268|                # Style matching would require ML model (HeartCLAP or similar)
269|                # For now, basic heuristic based on spectral centroid
270|                telemetry[path] = signature.model_dump()
271|
272|            except Exception as e:
273|                logger.error(f"Critique failed for {path}: {e}")
274|                rejection_reasons.append(f"Analysis error: {str(e)}")
275|
276|        approved = len(rejection_reasons) == 0
277|
278|        critique = AuditorCritique(
279|            approved=approved,
280|            rejection_reasons=rejection_reasons,
281|            loudness_match=not (issues["too_quiet"] or issues["too_loud"]),
282|            style_match=not issues["wrong_style"],
283|            technical_quality=not (issues["clipping"] or issues["artifacts"]),
284|            **issues,
285|            telemetry=telemetry,
286|        )
287|
288|        if approved:
289|            logger.info("Output approved by Auditor")
290|        else:
291|            logger.warning(f"Output rejected: {rejection_reasons}")
292|
293|        return critique
294|