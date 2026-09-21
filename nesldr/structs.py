from ctypes import *

"""

    Nintendo Entertainment System (NES) loader module
    ------------------------------------------------------
    Copyright 2006, Dennis Elser (dennis@backtrace.de)

"""


# ----------------------------------------------------------------------
#
#      general NES info:
#


RAM_START_ADDRESS = 0x0
RAM_SIZE = 0x2000

IOREGS_START_ADDRESS = 0x2000
IOREGS_SIZE = 0x2020

EXPROM_START_ADDRESS = 0x4020
EXPROM_SIZE = 0x1FE0

SRAM_START_ADDRESS = 0x6000
SRAM_SIZE = 0x2000

# start address and size of a trainer, if present
TRAINER_START_ADDRESS = 0x7000
TRAINER_SIZE = 0x0200

ROM_START_ADDRESS = 0x8000
ROM_SIZE = 0x8000

PRG_PAGE_SIZE = 0x4000
CHR_PAGE_SIZE = 0x2000


PRG_ROM_BANK_SIZE = PRG_PAGE_SIZE
PRG_ROM_8K_BANK_SIZE = 0x2000
PRG_ROM_BANK_LOW_ADDRESS = ROM_START_ADDRESS
PRG_ROM_BANK_HIGH_ADDRESS = PRG_ROM_BANK_LOW_ADDRESS + PRG_ROM_BANK_SIZE
PRG_ROM_BANK_8000 = 0x8000
PRG_ROM_BANK_A000 = 0xA000
PRG_ROM_BANK_C000 = 0xC000
PRG_ROM_BANK_E000 = 0xE000


CHR_ROM_BANK_SIZE = CHR_PAGE_SIZE
CHR_ROM_BANK_ADDRESS = RAM_START_ADDRESS


# start address of vectors
NMI_VECTOR_START_ADDRESS = 0xFFFA
RESET_VECTOR_START_ADDRESS = 0xFFFC
IRQ_VECTOR_START_ADDRESS = 0xFFFE


# PPU RAM layout bottom-up

PATTERN_TABLE_SIZE = 0x1000
ATTRIBUTE_TABLE_SIZE = 0x40
NAME_TABLE_SIZE = 0x3C0
MIRRORS_0_SIZE = 0xF00
MIRRORS_1_SIZE = 0xE0
MIRRORS_2_SIZE = 0xC000

PALETTE_SIZE = 0x10


PATTERN_TABLE_0_ADDRESS = 0x0
PATTERN_TABLE_1_ADDRESS = 0x1000

NAME_TABLE_0_ADDRESS = 0x2000
ATTRIBUTE_TABLE_0_ADDRESS = 0x23C0

NAME_TABLE_1_ADDRESS = 0x2400
ATTRIBUTE_TABLE_1_ADDRESS = 0x27C0

NAME_TABLE_2_ADDRESS = 0x2800
ATTRIBUTE_TABLE_2_ADDRESS = 0x2BC0

NAME_TABLE_3_ADDRESS = 0x2C00
ATTRIBUTE_TABLE_3_ADDRESS = 0x2CF0

MIRRORS_0_ADDRESS = 0x3000

IMAGE_PALETTE_ADDRESS = 0x3F00

SPRITE_PALETTE_ADDRESS = 0x3F10

MIRRORS_1_ADDRESS = 0x3F20

MIRRORS_2_ADDRESS = 0x4000


# ----------------------------------------------------------------------
#
#      iNES file format specific information
#

# structure of iNES header
class ines_hdr(Structure):
    _pack_ = 1
    _fields_ = [
        ('id', c_char * 0x3),                          # NES
        ('term', c_ubyte),                             # 0x1A
        # iNES page count / NES 2.0 PRG-ROM size LSB
        ('prg_page_count_16k', c_ubyte),
        # iNES page count / NES 2.0 CHR-ROM size LSB
        ('chr_page_count_8k', c_ubyte),
        # flags describing ROM image
        ('rom_control_byte_0', c_ubyte),
        # flags describing ROM image
        ('rom_control_byte_1', c_ubyte),
        # byte 8: iNES RAM count / NES 2.0 mapper and submapper
        ('ram_bank_count_8k', c_ubyte),
        # bytes 9-15: iNES flags/padding or NES 2.0 extension fields
        ('reserved', c_ubyte * 7),
    ]

    def is_nes2_hdr(self):
        return (self.rom_control_byte_1 & 0x0C) == 0x08

    @property
    def mapper_number(self):
        mapper = INES_MASK_MAPPER_VERSION(
            self.rom_control_byte_0, self.rom_control_byte_1)
        if self.is_nes2_hdr():
            mapper |= (self.ram_bank_count_8k & 0x0F) << 8
        return mapper

    @property
    def submapper_number(self):
        return (self.ram_bank_count_8k >> 4) if self.is_nes2_hdr() else 0

    def _rom_size(self, lsb, msb, page_size):
        if not self.is_nes2_hdr():
            return lsb * page_size
        if msb == 0x0F:
            return (1 << (lsb >> 2)) * (2 * (lsb & 0x03) + 1)
        return ((msb << 8) | lsb) * page_size

    @property
    def prg_rom_size(self):
        return self._rom_size(self.prg_page_count_16k,
                              self.reserved[0] & 0x0F, PRG_PAGE_SIZE)

    @property
    def chr_rom_size(self):
        return self._rom_size(self.chr_page_count_8k,
                              self.reserved[0] >> 4, CHR_PAGE_SIZE)

    # ----------------------------------------------------------------------
    #
    #      check if ROM image header is corrupt
    #
    def is_corrupt_ines_hdr(self):
        if self.is_nes2_hdr():
            return False
        return any(_ != 0 for _ in self.reserved[2:])

    # ----------------------------------------------------------------------
    #
    #      fix iNES header internally
    #

    def fix_ines_hdr(self):
        if self.is_nes2_hdr():
            return
        if(bytes(self)[7:] in (b"DiskDude!", b"DiskDude\x00")):
            self.rom_control_byte_1 = 0
            self.ram_bank_count_8k = 0
            self.reserved[0] = 0
            self.reserved[1] = 0
        self.reserved[2:] = b'\x00' * (sizeof(self.reserved) - 2)
        return


# size of iNES header
INES_HDR_SIZE = sizeof(ines_hdr)


# node name for iNES header
INES_HDR_NODE = "$ iNES ROM header"

BANK_NUM_8000 = "$ Bank 8000"
BANK_NUM_C000 = "$ Bank C000"

# macros for masking control byte (cb) flags of the header


def INES_MASK_V_MIRRORING(cb):
    return (cb & 0x1)


def INES_MASK_H_MIRRORING(cb):
    return not INES_MASK_V_MIRRORING(cb)


def INES_MASK_SRAM(cb):
    return ((cb & 0x2) >> 1)


def INES_MASK_TRAINER(cb):
    return ((cb & 0x4) >> 2)


def INES_MASK_VRAM_LAYOUT(cb):
    return ((cb & 0x8) >> 3)


def INES_MASK_MAPPER_VERSION(cb0, cb1):
    # macro for getting the version of the mapper used by ROM image
    return (((cb0 & 0xF0) >> 4) | (cb1 & 0xF0))
