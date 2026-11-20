"""Derive the standalone Post-NOC intake showcase from the full Structured CMC review page.

Reads  showcases/pqi-structured-cmc-review.html
Writes showcases/pqi-post-noc-intake.html

The new page keeps the same embedded FHIR data, logic and inspector, but:
  - opens directly on the Post-NOC intake view (only view in the side pane),
  - sends any link to another review view to the full Structured CMC review page,
  - hides the dossier search (it targets the other views).
Run from the repo root:  python3 sakura-bloom-r2/showcase/build_postnoc_page.py
"""
import os, sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src = os.path.join(root, "showcases", "pqi-structured-cmc-review.html")
dst = os.path.join(root, "showcases", "pqi-post-noc-intake.html")
s = open(src, encoding="utf-8").read()

def sub(old, new, count=1):
    global s
    if old not in s:
        sys.exit(f"build_postnoc_page: expected text not found: {old[:70]!r}")
    s = s.replace(old, new, count)

sub("<title>Structured CMC Review – Sakura Bloom</title>",
    "<title>Post-NOC Change Intake – Sakura Bloom</title>")
sub("<small>Structured CMC Review</small>", "<small>Post-NOC Change Intake</small>")
sub('<div class="search">', '<div class="search" style="visibility:hidden">')

# Only the intake view in the pane; it is also the default route.
start = s.index("const VIEWS = [")
end = s.index("];", start) + 2
s = s[:start] + 'const VIEWS = [\n  ["post-noc-intake", "Post-NOC intake", viewIntake],\n];' + s[end:]

# Links to any other view open the full review page.
sub('function go(v) { if (location.hash === "#" + v) route(); else location.hash = v; }',
    'function go(v) { if (v !== "post-noc-intake") { location.href = "pqi-structured-cmc-review.html#" + v; return; } if (location.hash === "#" + v) route(); else location.hash = v; }')

# Pane footer: point to the full review.
sub('<p class="pane-foot">',
    '<p class="pane-foot"><a href="pqi-structured-cmc-review.html">Open the full Structured CMC review →</a><br><br>')

open(dst, "w", encoding="utf-8").write(s)
print("written", dst, len(s))
