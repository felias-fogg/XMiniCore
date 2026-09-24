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
import re
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


COMPILE_RECIPES = ("recipe.c.o.pattern", "recipe.cpp.o.pattern", "recipe.S.o.pattern",
                   "recipe.ar.pattern", "recipe.c.combine.pattern",
                   "recipe.preproc.macros")


def build_properties(platform: dict, boards: dict) -> set:
    """
    Which properties a compile recipe reads, directly or through others. The
    recipes rarely name a menu's property themselves: a menu sets build.xyz,
    something composes build.extra_flags out of it, and only that appears in the
    recipe. So follow the references until nothing new turns up.
    """
    reference = re.compile(r"\{([\w.]+)\}")
    known = dict(platform)
    for key, value in boards.items():          # a menu may compose things as well
        known.setdefault(key.split(".menu.")[-1].split(".", 1)[-1], value)
    used, pending = set(), []
    for key in COMPILE_RECIPES:
        pending += reference.findall(platform.get(key, ""))
    while pending:
        name = pending.pop()
        if name in used:
            continue
        used.add(name)
        pending += reference.findall(known.get(name, ""))
    return used


def affects_the_build(boards: dict, menu: str, relevant: set) -> bool:
    """Whether any option of this menu sets something a compile recipe reads."""
    marker = f".menu.{menu}."
    for key in boards:
        if marker not in key:
            continue
        tail = key.split(marker, 1)[1]
        if "." not in tail:
            continue
        prop = tail.split(".", 1)[1]
        if prop.startswith("compiler.") or prop in relevant:
            return True
    return False


def count_combinations(offered: dict) -> int:
    """How many combinations there would be, without building the list."""
    total = 1
    for options in offered.values():
        total *= len(options)
    return total


def menus_worth_varying(boards: dict, platform: dict) -> list:
    """
    The menus that can change the binary, saying which ones are left out. The
    others still get built, just in one of their settings rather than all.
    """
    relevant = build_properties(platform, boards)
    every = sorted({k.split(".menu.")[1].split(".")[0] for k in boards
                    if ".menu." in k})
    wanted = [m for m in every if affects_the_build(boards, m, relevant)]
    skipped = [m for m in every if m not in wanted]
    if skipped:
        print(f"not varying {', '.join(skipped)}: no compile recipe reads what they set")
    return wanted


def menu_options(boards: dict, board: str) -> dict:
    """
    Which menus this board offers and which options each has, in the order they
    are declared: the first one is what the IDE offers by default.
    """
    offered: dict = {}
    prefix = f"{board}.menu."
    for key in boards:
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].split(".")
        if len(parts) >= 2 and parts[1] not in offered.setdefault(parts[0], []):
            offered[parts[0]].append(parts[1])
    return offered


def as_fqbn_part(menus: list, picked: tuple) -> str:
    """Turn one choice per menu into the tail of an FQBN."""
    return ",".join(f"{m}={o}" for m, o in zip(menus, picked))


def combinations(offered: dict) -> list:
    """Every combination of the menus, as a list of 'menu=option' strings."""
    if not offered:
        return [""]
    menus = sorted(offered)
    return [as_fqbn_part(menus, picked)
            for picked in itertools.product(*(offered[m] for m in menus))]


def each_value_once(offered: dict) -> list:
    """
    Enough combinations for every option of every menu to be built at least once.
    Counting all menus up at the same time needs as many builds as the longest
    menu has options, rather than their product. Catches an option that is broken
    by itself, not two that only go wrong together.
    """
    if not offered:
        return [""]
    menus = sorted(offered)
    longest = max(len(offered[m]) for m in menus)
    return [as_fqbn_part(menus, tuple(offered[m][i % len(offered[m])] for m in menus))
            for i in range(longest)]


def defaults_only(offered: dict) -> list:
    """
    One combination, the one the IDE starts with. Enough where the point is the
    platform rather than the options: the hook scripts and the handling of paths
    do not depend on which menu entry is chosen.
    """
    if not offered:
        return [""]
    menus = sorted(offered)
    return [as_fqbn_part(menus, tuple(offered[m][0] for m in menus))]


def write_sketch(folder: str) -> str:
    """
    Put a sketch where arduino-cli can build it, below a directory whose name has
    a blank in it. The sketch name itself must not have one, but everything above
    it may, and that is where an unquoted path in a recipe shows up.
    """
    sketch = os.path.join(folder, "with blank", "compile_all_probe")
    os.makedirs(sketch, exist_ok=True)
    with open(os.path.join(sketch, "compile_all_probe.ino"), "w", encoding="utf-8") as out:
        out.write(SKETCH)
    return sketch


FULL_PRODUCT_LIMIT = 64          # above this, 'auto' stops building every combination


def chosen_combinations(offered: dict, coverage: str) -> list:
    """The combinations this coverage asks for."""
    if coverage == "one":
        return defaults_only(offered)
    if coverage == "each-value":
        return each_value_once(offered)
    if coverage == "full" or count_combinations(offered) <= FULL_PRODUCT_LIMIT:
        return combinations(offered)
    return each_value_once(offered)


def compile_one(sketch: str, fqbn: str, quiet: bool) -> bool:
    """Build one combination, saying what went wrong when it did."""
    build = os.path.join(os.path.dirname(sketch), "build path")
    done = subprocess.run(["arduino-cli", "compile", "--clean", "-b", fqbn,
                           "--build-path", build, sketch],
                          capture_output=True, text=True, check=False)
    if done.returncode == 0:
        if not quiet:
            print(f"  ok      {fqbn}")
        return True
    print(f"  FAILED  {fqbn}")
    print("    " + (done.stderr or done.stdout).strip().replace("\n", "\n    "))
    return False


def main() -> int:
    """Build every combination and report which ones did not come through."""
    parser = argparse.ArgumentParser(description="compile for every board and menu")
    parser.add_argument("--fqbn-prefix", required=True, help="e.g. XMiniCore:avr")
    parser.add_argument("--root", help="the core's folder (default: the one above this)")
    parser.add_argument("--menus", help="only vary these menus, comma separated")
    parser.add_argument("--all-menus", action="store_true",
                        help="also vary menus that cannot change the binary")
    parser.add_argument("--coverage", default="auto",
                        choices=["auto", "full", "each-value", "one"],
                        help="how much to build: every combination, every option "
                             "at least once, or just the default one. 'auto' takes "
                             "the full product while it stays small")
    parser.add_argument("--quiet", action="store_true", help="only report failures")
    args = parser.parse_args()

    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    boards = properties(os.path.join(root, "boards.txt"))
    platform = properties(os.path.join(root, "platform.txt"))
    wanted = args.menus.split(",") if args.menus else None
    if wanted is None and not args.all_menus:
        wanted = menus_worth_varying(boards, platform)

    with tempfile.TemporaryDirectory() as folder:
        sketch = write_sketch(folder)
        every = []
        for board in board_ids(boards):
            offered = menu_options(boards, board)
            if wanted is not None:
                offered = {m: o for m, o in offered.items() if m in wanted}
            for combination in chosen_combinations(offered, args.coverage):
                fqbn = f"{args.fqbn_prefix}:{board}"
                every.append(fqbn + (f":{combination}" if combination else ""))
        failed = [fqbn for fqbn in every if not compile_one(sketch, fqbn, args.quiet)]

    print(f"{len(every)} combination(s), {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
