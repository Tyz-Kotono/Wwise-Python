import subprocess
import re

def momentary_max(audio_path: str) -> float | None:
    cmd = [
        "ffmpeg",
        "-loglevel", "info",
        "-nostats",
        "-i", audio_path,
        "-filter_complex", "ebur128",
        "-f", "null",
        "-"
    ]

    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    values = []
    pattern = re.compile(r"\bM:\s*(-?\d+(?:\.\d+)?)")

    for line in proc.stderr:
        match = pattern.search(line)
        if match:
            values.append(float(match.group(1)))

    proc.wait()
    return max(values) if values else None


audio = "ITU BS 1770-4 - Stereo -69.5 LUFS Absolute Gate Test.wav"

m_max = momentary_max(audio)

if m_max is None:
    print("Momentary Max: N/A")
else:
    print(f"Momentary Max: {m_max:.2f} LUFS")