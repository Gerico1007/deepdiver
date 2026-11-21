"""
Transcribe one audio or video file to timed lines, for `studio keep`.

Run by path with a Python that has faster-whisper and numpy (DeepDiver does
not need them itself):

    <python> -I transcribe_worker.py <media> <out.txt> [model]

Writes one "[mm:ss] text" line per segment to <out.txt>, atomically. Audio is
decoded with ffmpeg, because some PyAV builds refuse faster-whisper's own
decoder call (gaia, 2026-10-16).
"""

import os
import subprocess
import sys


def main(argv):
    if len(argv) < 3:
        print("usage: transcribe_worker.py <media> <out.txt> [model]", file=sys.stderr)
        return 2
    src, out = argv[1], argv[2]
    model_name = argv[3] if len(argv) > 3 else "base"
    import numpy as np
    from faster_whisper import WhisperModel

    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         check=True, capture_output=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(audio, language="en", vad_filter=True)
    tmp = out + ".part"
    with open(tmp, "w", encoding="utf-8") as fh:
        for s in segments:
            minutes, seconds = divmod(int(s.start), 60)
            fh.write(f"[{minutes:02d}:{seconds:02d}] {s.text.strip()}\n")
    os.replace(tmp, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
