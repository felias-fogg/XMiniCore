#!/usr/bin/env python3
"""
Check that the prebuild hook really picks the '#pragma arduino ...' lines out of
a sketch and writes them where the build reads them from.

    python3 extras/check_hooks.py --fqbn XMiniCore:avr:atmega328p_xplained_mini

The hook exists in two versions, a shell one and a batch one, and they only ever
run on their own platform. A failure is silent by nature: the options file stays
empty, the flags are quietly dropped and the build succeeds all the same. So
this builds a sketch whose pragmas are known and looks at what came out.

Needs arduino-cli with the core installed. Standard library apart from that.
"""

import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_core import working_directory     # pylint: disable=wrong-import-position

EXPECTED = {
    "debug_flags": "-DPROBE_DEBUG",
    "release_flags": "-DPROBE_RELEASE",
    "cpp_flags": "-DPROBE_CPP",
}

SKETCH = """
#pragma arduino debug_flags {debug_flags}
#pragma arduino release_flags {release_flags}
#pragma arduino cpp_flags {cpp_flags}

void setup() {{ }}
void loop() {{ }}
""".format(**EXPECTED)


def build(fqbn: str, folder: str) -> str:
    """Compile the probe sketch and return the build directory."""
    sketch = os.path.join(folder, "with blank", "hook_probe")
    os.makedirs(sketch, exist_ok=True)
    with open(os.path.join(sketch, "hook_probe.ino"), "w", encoding="utf-8") as out:
        out.write(SKETCH)
    build_path = os.path.join(folder, "with blank", "build path")
    done = subprocess.run(["arduino-cli", "compile", "--clean", "-b", fqbn,
                           "--build-path", build_path, sketch],
                          capture_output=True, text=True, check=False)
    if done.returncode != 0:
        print("the probe sketch did not compile:")
        print((done.stderr or done.stdout).strip())
        sys.exit(1)
    return build_path


def main() -> int:
    """Build the probe and compare the options files with what the sketch said."""
    parser = argparse.ArgumentParser(description="check the prebuild hook")
    parser.add_argument("--fqbn", required=True, help="the board to build for")
    parser.add_argument("--work-dir", metavar="DIR",
                        help="where to build, a temporary directory by default")
    args = parser.parse_args()

    if shutil.which("arduino-cli") is None:
        print("arduino-cli is not on PATH")
        return 1

    with working_directory(args.work_dir) as folder:
        build_path = build(args.fqbn, folder)
        wrong = []
        for flag, expected in sorted(EXPECTED.items()):
            path = os.path.join(build_path, f"options.{flag}")
            if not os.path.exists(path):
                print(f"  MISSING  options.{flag}")
                wrong.append(flag)
                continue
            with open(path, encoding="utf-8", errors="replace") as src:
                content = src.read().strip()
            if expected in content:
                print(f"  ok       options.{flag}: {content!r}")
            else:
                print(f"  WRONG    options.{flag}: {content!r}, expected {expected!r}")
                wrong.append(flag)

    if wrong:
        print(f"the hook did not deliver {', '.join(wrong)}")
        return 1
    print("the prebuild hook works on this platform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
