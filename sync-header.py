#!/usr/bin/env python3
"""
sync-header.py — Injects header.html into all catalogue pages.

Run this script whenever you edit header.html.
It replaces everything between the markers:
  <!-- HEADER:BEGIN --> ... <!-- HEADER:END -->
with the content of header.html.

Usage:  python3 sync-header.py
"""

import glob
import sys
import os

HEADER_FILE = "header.html"
BEGIN_MARKER = "<!-- HEADER:BEGIN -->"
END_MARKER = "<!-- HEADER:END -->"

def main():
    # Read the header partial
    if not os.path.exists(HEADER_FILE):
        print(f"ERROR: {HEADER_FILE} not found.")
        sys.exit(1)

    with open(HEADER_FILE, "r") as f:
        header_html = f.read()

    replacement = f"{BEGIN_MARKER}\n{header_html}{END_MARKER}"

    html_files = glob.glob("*.html")
    updated = 0

    for file_name in sorted(html_files):
        if file_name == HEADER_FILE:
            continue

        with open(file_name, "r") as f:
            content = f.read()

        # Check if the file has markers
        if BEGIN_MARKER in content and END_MARKER in content:
            begin_idx = content.index(BEGIN_MARKER)
            end_idx = content.index(END_MARKER) + len(END_MARKER)
            new_content = content[:begin_idx] + replacement + content[end_idx:]

            if new_content != content:
                with open(file_name, "w") as f:
                    f.write(new_content)
                print(f"  ✓ Updated {file_name}")
                updated += 1
            else:
                print(f"  · {file_name} (already up to date)")
        else:
            print(f"  ✗ {file_name} — missing markers, skipped")

    print(f"\nDone. {updated} file(s) updated.")


if __name__ == "__main__":
    main()
