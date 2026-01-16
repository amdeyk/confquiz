#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
TEMPLATES = [
    ROOT / "templates" / "presenter_dashboard.html",
    ROOT / "templates" / "display.html",
]

CDN_SRC = "https://unpkg.com/livekit-client/dist/livekit-client.min.js"
LOCAL_SRC = "/static/js/livekit-client.min.js"
ALIAS_LINE = "  window.livekit = window.livekit || window.LiveKitClient || window.LiveKit;\n"


def _normalize_livekit_if_line(line: str) -> str:
    if "if (!window.livekit" not in line:
        return line
    indent = re.match(r"\s*", line).group(0)
    return f"{indent}if (!window.livekit) {{"


def patch_text(text: str) -> str:
    # Force local LiveKit client usage.
    text = text.replace(CDN_SRC, LOCAL_SRC)

    # Remove inline alias script tags from earlier hotfixes.
    text = re.sub(
        r'\n?\s*<script>\s*window\.livekit\s*=\s*window\.livekit\s*\|\|\s*window\.LiveKitClient\s*\|\|\s*window\.LiveKit\s*;\s*</script>\s*',
        "\n",
        text,
        flags=re.M,
    )

    # Remove duplicated alias lines, then re-insert once in the correct place.
    text = re.sub(
        r'^\s*window\.livekit\s*=\s*window\.livekit\s*\|\|\s*window\.LiveKitClient\s*\|\|\s*window\.LiveKit\s*;\s*\n',
        "",
        text,
        flags=re.M,
    )

    # Fix any corrupted LiveKit checks.
    lines = text.splitlines()
    lines = [_normalize_livekit_if_line(line) for line in lines]
    text = "\n".join(lines)

    # Insert alias line after the inline script tag that follows the LiveKit script include.
    if "window.livekit = window.livekit" not in text:
        idx = text.find(LOCAL_SRC)
        if idx != -1:
            script_idx = text.find("<script>", idx)
            if script_idx != -1:
                insert_pos = script_idx + len("<script>")
                text = text[:insert_pos] + "\n" + ALIAS_LINE + text[insert_pos:]

    return text


def patch_file(path: Path) -> bool:
    if not path.exists():
        print(f"[WARN] Missing: {path}")
        return False
    original = path.read_text(encoding="utf-8")
    updated = patch_text(original)
    if updated == original:
        print(f"[OK] No change: {path}")
        return False
    # Preserve trailing newline if present.
    if original.endswith("\n") and not updated.endswith("\n"):
        updated += "\n"
    path.write_text(updated, encoding="utf-8")
    print(f"[OK] Patched: {path}")
    return True


def main() -> int:
    changed = False
    for path in TEMPLATES:
        changed = patch_file(path) or changed

    client_file = ROOT / "static" / "js" / "livekit-client.min.js"
    if not client_file.exists():
        print(f"[WARN] Missing LiveKit client bundle: {client_file}")
    else:
        size = client_file.stat().st_size
        if size < 100_000:
            print(f"[WARN] LiveKit client bundle looks too small ({size} bytes).")

    if not changed:
        print("[INFO] No template changes applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
