# CHANGELOG

## v1.2.0
- rolled back to GCC 7.3.0 (because under 15.1.0 GDB cannot display a local variable correctly)
- added support for native cortex-debug by adding launch.json generation when compiling

## v1.1.1

- fixed order of options
- added cpp_flags

## v1.1.0

- pragma added (so that one can choose the language variant)

## v1.0.0

- AVR-GCC 15.1 toolchain added

## v0.9.9

- first working version