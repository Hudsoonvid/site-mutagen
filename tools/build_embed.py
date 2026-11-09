#!/usr/bin/env python3
"""Build embed.html: one self-contained page for Google Sites (Insert > Embed > Embed code).

Bakes additions.json and any widgets into index.html, so the page needs no
network access and loads anywhere Google Sites loads.
"""
import json
import pathlib
import re

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

data = f"<script>window.MUTAGEN_DATA={to_js(items)};window.MUTAGEN_WIDGETS={to_js(widgets)};</script>\n  "
(root / "embed.html").write_text(html.replace(marker, data + marker), encoding="utf-8", newline="\n")
print(f"embed.html: {len(items)} additions, {len(widgets)} widgets")
