#!/usr/bin/env python3
"""
Print the changelog section for one version, to be used as release notes.

    python3 extras/changelog_entry.py v1.3.1
"""

import os
import re
import sys


def main() -> int:
    """Find the heading for the version and print what follows it."""
    if len(sys.argv) != 2:
        print("usage: changelog_entry.py <version>", file=sys.stderr)
        return 1
    version = sys.argv[1].lstrip("v")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "CHANGELOG.md")
    with open(path, encoding="utf-8", errors="replace") as src:
        lines = src.read().splitlines()

    heading = re.compile(rf"^(#+)\s*v?{re.escape(version)}\s*$")
    collected, level = [], None
    for line in lines:
        if level is None:
            found = heading.match(line)
            if found:
                level = len(found.group(1))
            continue
        if re.match(rf"^#{{1,{level}}}\s", line):
            break
        collected.append(line)

    if level is None:
        print(f"CHANGELOG.md has no entry for {version}", file=sys.stderr)
        return 1
    print("\n".join(collected).strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
