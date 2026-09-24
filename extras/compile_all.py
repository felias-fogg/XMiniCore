#!/usr/bin/env python3
"""
Compile a sketch for every board of the core, in every combination its menus
offer. A board entry that is wrong in boards.txt or platform.txt usually shows
up here and nowhere else, because nobody builds for every combination by hand.

    python3 extras/compile_all.py --fqbn-prefix XMiniCore:avr
    python3 extras/compile_all.py --fqbn-prefix XMiniCore:avr --menus clock,LTO

Needs arduino-cli with the core installed. Standard library apart from that.
"""

import argparse
import itertools
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_core import properties, board_ids      # pylint: disable=wrong-import-position

SKETCH = """
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
}
"""


def menu_options(boards: dict, board: str) -> dict:
    """Which menus this board offers, and which options each of them has."""
    offered: dict = {}
    prefix = f"{board}.menu."
    for key in boards:
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].split(".")
        if len(parts) >= 2:
            offered.setdefault(parts[0], set()).add(parts[1])
    return {menu: sorted(options) for menu, options in offered.items()}


def combinations(offered: dict) -> list:
    """Every combination of the menus, as a list of 'menu=option' strings."""
    if not offered:
        return [""]
    menus = sorted(offered)
    return [",".join(f"{m}={o}" for m, o in zip(menus, picked))
            for picked in itertools.product(*(offered[m] for m in menus))]


def write_sketch(folder: str) -> str:
    """Put a sketch that uses the usual suspects where arduino-cli can build it."""
    sketch = os.path.join(folder, "compile_all_probe")
    os.makedirs(sketch, exist_ok=True)
    with open(os.path.join(sketch, "compile_all_probe.ino"), "w", encoding="utf-8") as out:
        out.write(SKETCH)
    return sketch


def main() -> int:
    """Build every combination and report which ones did not come through."""
    parser = argparse.ArgumentParser(description="compile for every board and menu")
    parser.add_argument("--fqbn-prefix", required=True, help="e.g. XMiniCore:avr")
    parser.add_argument("--root", help="the core's folder (default: the one above this)")
    parser.add_argument("--menus", help="only vary these menus, comma separated")
    parser.add_argument("--quiet", action="store_true", help="only report failures")
    args = parser.parse_args()

    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    boards = properties(os.path.join(root, "boards.txt"))
    wanted = args.menus.split(",") if args.menus else None

    failed, count = [], 0
    with tempfile.TemporaryDirectory() as folder:
        sketch = write_sketch(folder)
        for board in board_ids(boards):
            offered = menu_options(boards, board)
            if wanted is not None:
                offered = {m: o for m, o in offered.items() if m in wanted}
            for combination in combinations(offered):
                fqbn = f"{args.fqbn_prefix}:{board}"
                if combination:
                    fqbn += f":{combination}"
                count += 1
                done = subprocess.run(["arduino-cli", "compile", "--clean", "-b", fqbn,
                                       sketch], capture_output=True, text=True, check=False)
                if done.returncode == 0:
                    if not args.quiet:
                        print(f"  ok      {fqbn}")
                else:
                    print(f"  FAILED  {fqbn}")
                    print("    " + (done.stderr or done.stdout).strip().replace("\n", "\n    "))
                    failed.append(fqbn)

    print(f"{count} combination(s), {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
