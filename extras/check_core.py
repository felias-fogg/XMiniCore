#!/usr/bin/env python3
"""
Check a core for the kinds of mistake that only show up when someone else uses it.

    python3 extras/check_core.py              # check the core this file belongs to
    python3 extras/check_core.py --tag v1.3.1 # and that it is ready to be released

Every check is about consistency inside the core, so it needs nothing but the
files themselves and the standard library. Errors make it exit non-zero;
warnings are printed and do not.
"""

import argparse
import os
import re
import sys

PROBLEMS: list = []
WARNINGS: list = []


def problem(text: str) -> None:
    """Record something that must be fixed before a release."""
    PROBLEMS.append(text)


def warn(text: str) -> None:
    """Record something worth a look that does not stop a release."""
    WARNINGS.append(text)


def properties(path: str) -> dict:
    """
    Read an Arduino properties file. Keys repeat the board id, values may contain
    anything, comments start with # at the beginning of a line.
    """
    found = {}
    if not os.path.exists(path):
        problem(f"{os.path.basename(path)} is missing")
        return found
    with open(path, encoding="utf-8", errors="replace") as src:
        for line in src:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            found[key.strip()] = value.strip()
    return found


def board_ids(boards: dict) -> list:
    """Every id that has a name is a board; menu declarations and the like are not."""
    return sorted(key[:-len(".name")] for key in boards
                  if key.endswith(".name") and key.count(".") == 1)


def defined_for(boards: dict, board: str, suffix: str) -> bool:
    """
    Whether a board has a property, directly or through one of its menu options:
    build.f_cpu, for instance, usually comes from the clock menu.
    """
    if f"{board}.{suffix}" in boards:
        return True
    prefix, ending = f"{board}.menu.", f".{suffix}"
    return any(k.startswith(prefix) and k.endswith(ending) for k in boards)


def check_boards(root: str, boards: dict) -> None:
    """Each board needs the properties a build depends on, and its variant folder."""
    for board in board_ids(boards):
        for suffix in ("build.mcu", "build.f_cpu", "build.board", "build.variant"):
            if not defined_for(boards, board, suffix):
                problem(f"board '{board}' has no {suffix}, not even through a menu")
        variant = boards.get(f"{board}.build.variant")
        if variant and not os.path.isdir(os.path.join(root, "variants", variant)):
            problem(f"board '{board}' uses variant '{variant}', which has no folder")


def check_menus(boards: dict) -> None:
    """
    A menu a board uses has to be declared at the top of boards.txt, and every
    option a board configures needs a label, or the IDE shows an empty entry.
    """
    declared = {key[len("menu."):] for key in boards
                if key.startswith("menu.") and key.count(".") == 1}
    used = {}
    for key in boards:
        parts = key.split(".")
        if len(parts) >= 4 and parts[1] == "menu":
            used.setdefault(parts[2], set()).add(parts[3])
    for menu in sorted(used):
        if menu not in declared:
            problem(f"menu '{menu}' is used by a board but never declared")
    for menu in sorted(declared - set(used)):
        warn(f"menu '{menu}' is declared but no board offers it")
    ids = set(board_ids(boards))
    for menu, options in sorted(used.items()):
        for option in sorted(options):
            ending = f".menu.{menu}.{option}"
            labels = [k for k in boards
                      if k.endswith(ending) and k[:-len(ending)] in ids]
            if not labels:
                problem(f"option '{option}' of menu '{menu}' has no label on any board")


def check_lto(boards: dict, platform: dict) -> None:
    """
    A core that offers LTO as a menu must not put -flto into the optimization
    flags: those are used whatever the menu says, so the switch would do nothing.
    """
    has_menu = any(k.startswith("menu.LTO") for k in boards)
    if not has_menu:
        return
    for key, value in platform.items():
        if key.startswith("compiler.optimization_flags") and "-flto" in value:
            problem(f"{key} contains -flto although there is an LTO menu, "
                    "so 'LTO disabled' would not disable anything")


def check_hook_scripts(root: str, platform: dict) -> None:
    """Every script a recipe calls has to be there, on every platform."""
    pattern = re.compile(r"\{runtime\.platform\.path\}[/\\]([\w/\\.-]+)")
    for key, value in platform.items():
        if not key.startswith("recipe."):
            continue
        for relative in pattern.findall(value):
            path = os.path.join(root, relative.replace("\\", "/"))
            if not os.path.exists(path):
                problem(f"{key} calls '{relative}', which does not exist")


def check_line_endings(root: str) -> None:
    """Windows batch files need CRLF, and git only keeps it with a rule for it."""
    attributes = os.path.join(root, ".gitattributes")
    rule = ""
    if os.path.exists(attributes):
        with open(attributes, encoding="utf-8", errors="replace") as src:
            rule = src.read()
    if ".bat" not in rule:
        for folder, _, files in os.walk(root):
            if ".git" in folder:
                continue
            if any(f.endswith(".bat") for f in files):
                problem("there are .bat files but .gitattributes has no rule for them, "
                        "so their CRLF line endings depend on whoever clones the core")
                return


def check_release(root: str, platform: dict, tag: str) -> None:
    """Before a release the version has to be stated in the two places that say it."""
    version = tag.lstrip("v")
    stated = platform.get("version")
    if stated != version:
        problem(f"platform.txt says version={stated}, but the tag says {version}")
    changelog = os.path.join(root, "CHANGELOG.md")
    if not os.path.exists(changelog):
        problem("CHANGELOG.md is missing")
        return
    with open(changelog, encoding="utf-8", errors="replace") as src:
        text = src.read()
    if not re.search(rf"^#+\s*v?{re.escape(version)}\s*$", text, re.MULTILINE):
        problem(f"CHANGELOG.md has no entry for {version}")


def main() -> int:
    """Run every check and report what came out of it."""
    parser = argparse.ArgumentParser(description="check a core for consistency")
    parser.add_argument("--root", help="the core's folder (default: the one above this)")
    parser.add_argument("--tag", help="also check that the core is ready for this tag")
    args = parser.parse_args()

    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    boards = properties(os.path.join(root, "boards.txt"))
    platform = properties(os.path.join(root, "platform.txt"))
    print(f"checking {root}")
    print(f"  {len(board_ids(boards))} boards, {len(platform)} platform properties")

    check_boards(root, boards)
    check_menus(boards)
    check_lto(boards, platform)
    check_hook_scripts(root, platform)
    check_line_endings(root)
    if args.tag:
        check_release(root, platform, args.tag)

    for text in WARNINGS:
        print(f"  warning: {text}")
    for text in PROBLEMS:
        print(f"  PROBLEM: {text}")
    if PROBLEMS:
        print(f"{len(PROBLEMS)} problem(s)")
        return 1
    print("no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
