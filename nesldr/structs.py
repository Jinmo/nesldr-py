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
        # number of PRG-ROM pages
        ('prg_page_count_16k', c_ubyte),
        # number of CHR-ROM pages
        ('chr_page_count_8k', c_ubyte),
        # flags describing ROM image
        ('rom_control_byte_0', c_ubyte),
        # flags describing ROM image
        ('rom_control_byte_1', c_ubyte),
        # not used by this loader currently
        ('ram_bank_count_8k', c_ubyte),
        # should all be zero (not checked by loader)
        ('reserved', c_ubyte * 7),
    ]

    # ----------------------------------------------------------------------
    #
    #      check if ROM image header is corrupt
    #
    def is_corrupt_ines_hdr(self):
        return any(_ != 0 for _ in self.reserved)

    # ----------------------------------------------------------------------
    #
    #      fix iNES header internally
    #

    def fix_ines_hdr(void):
        diskdude = b"DiskDude\x00"

        if(self.rom_control_byte_1[0] == diskdude[0] and self.ram_bank_count_8k == diskdude[1] and self.reserved == diskdude[2:]):
            self.rom_control_byte_1[:] = b'\x00' * 9
        self.reserved[:] = b'\x00' * sizeof(self.reserved)
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
