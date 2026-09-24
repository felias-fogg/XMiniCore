# CHANGELOG
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