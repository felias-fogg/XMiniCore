# CHANGELOG
## v1.3.3
- The release workflow now compiles on Linux, macOS and Windows, each time
  below paths that contain a blank, so the hook scripts are exercised where
  they are actually used
- pragma.sh called the compiler unquoted, and its three rm calls had the
  wildcard inside the quotes, so the cached object files it meant to remove
  when the flags change were never removed
- A check that the prebuild hook really delivers the '#pragma arduino' flags,
  run on each of the three platforms. A hook that stops working is silent: the
  options file stays empty, the flags are dropped and the build succeeds
- pragma.bat ran 'echo | findstr' plus two subroutine calls for every line of
  the preprocessed source, tens of thousands of them, three times per compile.
  A single findstr over the file now leaves the few lines that can match. This
  was not a CI problem: it cost every Windows user minutes on every build
- The Windows job keeps Defender away from the build directories, which is
  what made it take forty minutes where Linux takes one
- compile_all.py knows three coverage levels and picks one: the full product
  while it stays small, otherwise every option at least once, which costs the
  longest menu rather than the product of all of them. Windows and macOS build
  one combination per board, because hook scripts and path handling do not
  depend on the menu choice
- compile_all.py works out which menus can change the binary and varies only
  those: debug and eeprom touch neither, so three quarters of the builds were
  the same binary over again (12 combinations instead of 48)
- Every release now offers the newest avrdude: the workflow adds it to the
  index before the core entry, which then depends on it (8.1 -> 8.3)

## v1.3.2
- The LTO menu was attached to a misspelled board id on the 168pb Xplained
  Mini, so that board never offered it
- A release workflow, a consistency check for the core (extras/check_core.py)
  and a compile run over every board and menu combination
  (extras/compile_all.py)

## v1.3.1
- The LTO menu now really switches LTO off: -flto was still in
  compiler.optimization_flags, so it was passed whatever the menu said,
  and only the archiver changed. With LTO in effect, avr-gcc 7.3 drops
  class information from the debug data.
- version= in platform.txt was still at 1.2.4

## v1.3.0
- LTO can now be manually enabled and disabled and is not any longer
  dependent on the "Optimize for Debug" setting.
- Windows batch files hardened against space in pathnames

## v1.2.4
- New PyAvrOCD version 1.5.8 (with new avr-gdb client 17.2.2
  that does not crash anymore in Ubuntu 24.04).

## v1.2.3
- New PyAvrOCD version 1.5.7

## v1.2.2

- Rolled back `launch.json` generation. This is now handled by _Arduino
  Maker Workshop_.

## v1.2.1
- Fixed naming glitch (GCC15 still in title)
- Fixing JSON problem under Windows: Double backslashes!
- New PyAvrOCD version


## v1.2.0
- rolled back to GCC 7.3.0 (because under 15.1.0 GDB cannot display a local variable correctly)
- added support for native cortex-debug by adding launch.json generation when compiling
- two configurations: pyavrocd and simavr

## v1.1.1

- fixed order of options
- added cpp_flags

## v1.1.0

- pragma added (so that one can choose the language variant)

## v1.0.0

- AVR-GCC 15.1 toolchain added

## v0.9.9

- first working version