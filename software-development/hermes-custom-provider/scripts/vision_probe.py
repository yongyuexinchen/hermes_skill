"""Probe any OpenAI-compatible endpoint for working vision support.

Generates a 64x64 solid-red PNG in-memory (no deps beyond stdlib) and asks
the model what color it is. Success criterion: answer mentions red/红.

Usage:
    python vision_probe.py <base_url> <api_key> <model>
Example:
    python vision_probe.py https://ark.cn-beijing.volces.com/api/v3 ark-xxx doubao-seed-2-1-turbo-260628

Pitfall this script encodes: some providers (Volcengine Ark) reject tiny
images (1x1 -> HTTP 400 with no useful body). 64x64 passes everywhere tested.
"""
import base64
import json
import struct
import sys
import urllib.error
import urllib.request
import zlib


def make_png(w: int, h: int, rgb: tuple) -> bytes:
    def chunk(t: bytes, d: bytes) -> bytes:
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    base_url, api_key, model = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3]
    png = base64.b64encode(make_png(64, 64, (255, 0, 0))).decode()
    req = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": "data:image/png;base64," + png}},
                    {"type": "text", "text": "这是什么颜色?一句话回答"},
                ],
            }],
            "max_tokens": 100,
        }).encode(),
        headers={"Authorization": "Bearer " + api_key,
                 "Content-Type": "application/json"},
    )
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
        answer = r["choices"][0]["message"]["content"]
        ok = ("红" in answer) or ("red" in answer.lower())
        print(("VISION OK: " if ok else "VISION SUSPECT (unexpected answer): ") + answer)
        return 0 if ok else 1
    except urllib.error.HTTPError as e:
        print("HTTP", e.code)
        print(e.read().decode(errors="replace")[:800])
        return 1


if __name__ == "__main__":
    sys.exit(main())
