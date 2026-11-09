#!/usr/bin/env python3
"""Build embed.html: one self-contained page for Google Sites (Insert > Embed > Embed code).

Bakes additions.json and any widgets into index.html, so the page needs no
network access and loads anywhere Google Sites loads.
"""
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

root = pathlib.Path(__file__).resolve().parent.parent
html = (root / "index.html").read_text(encoding="utf-8")
items = json.loads((root / "additions.json").read_text(encoding="utf-8"))

widgets = {}
for item in items:
    path = item.get("widget")
    if isinstance(path, str) and re.fullmatch(r"widgets/[a-z0-9-]+\.html", path):
        file = root / path
        if file.is_file():
            widgets[path] = file.read_text(encoding="utf-8")


def to_js(value):
    # Escaping "<" keeps request text from ever closing the script tag.
    return json.dumps(value, ensure_ascii=True).replace("<", "\\u003c")


marker = "<script>\n    (function () {"
if html.count(marker) != 1:
    raise SystemExit("Could not find the main script in index.html")

used = {item.get("widget") for item in items}
for file in (root / "widgets").glob("*.html"):
    if f"widgets/{file.name}" not in used:
        file.unlink()

for required in ('id="additions"', 'id="cv"', 'id="tl-range"', "forms.gle/joeZed9KM3tsd2Td8", "requested-by"):
    if required not in html:
        raise SystemExit(f"Not publishing: index.html is missing {required}")

node = shutil.which("node")
if node:
    for number, script in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S), 1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
            handle.write(script)
        checked = subprocess.run([node, "--check", handle.name], capture_output=True, text=True)
        pathlib.Path(handle.name).unlink()
        if checked.returncode != 0:
            raise SystemExit(f"Not publishing: script {number} in index.html has an error:\n{checked.stderr[-800:]}")

status_file = root / "status.json"
status = json.loads(status_file.read_text(encoding="utf-8")) if status_file.is_file() else {}
data = f"<script>window.MUTAGEN_DATA={to_js(items)};window.MUTAGEN_WIDGETS={to_js(widgets)};window.MUTAGEN_STATUS={to_js(status)};</script>\n  "
(root / "embed.html").write_text(html.replace(marker, data + marker), encoding="utf-8", newline="\n")
print(f"embed.html: {len(items)} additions, {len(widgets)} widgets")
