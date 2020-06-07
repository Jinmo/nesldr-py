# known bugs:

- if ROM images are not aligned properly (see nes.h),
  the loader won't load the ROM correctly. Also, if
  actually less pages than given in the iNES header
  are present in the ROM, the loader will fail.
- the loader doesn't initialize RAM
- exp rom is not supported yet
- not all mappers have been tested, please open an
  issue on github if you experience any problems
- swapping banks is not supported, by the loader itself.
  Please check out the [bankswitch](https://github.com/patois/bankswitch) plugin on github
  (untested on most recent IDA versions)
- if both SRAM and a trainer are present, the loader
  only creates an SRAM segment since according to documentation,
  the trainer is mapped to a part of the SRAM segment.
  Trainers are supported by emulators only but *not*
  on real hardware
