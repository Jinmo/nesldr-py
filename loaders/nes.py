"""
    Nintendo Entertainment System (NES) loader module
    ------------------------------------------------------
    Copyright 2006, Dennis Elser (dennis@backtrace.de)


    IDA Pro loader module for Nintendo Enternainment System
    (NES) ROM images in iNES file format.


    todo list:
    ----------
    - detect write access to PRG ROM and EXP ROM area and
      autocomment it as bank swapping mechanism ?

    - implement a bank-switching-plugin?

    - further division of several memory segments into
      "subsegments" ?


    license:
    --------

    - freeware, copyright messages have to stay intact.



    Copy compiled loader to idadir%/loaders/nes.ldw


    Please send me an e-mail if you find any bugs!

    (c) 2006, Dennis Elser (dennis@backtrace.de)

"""

from nesldr.structs import *
from nesldr.ioregs import *
from nesldr.mappers import *
import ida_netnode
from ida_loader import file2base, FILEREG_PATCHABLE
from ida_idp import ph, PLFM_6502, set_processor_type, SETPROC_LOADER_NON_FATAL
from ida_kernwin import msg, warning
from ida_segment import add_segm, set_segm_addressing, getseg
from ida_bytes import del_items, create_data, byte_flag, word_flag, set_cmt, get_word
from ida_name import set_name
from ida_entry import add_entry
from ida_offset import op_offset
from ida_lines import add_extra_line
from ida_idaapi import get_inf_structure
from ida_nalt import get_root_filename

inf = get_inf_structure()


def YES_NO(condition):
    return ("yes" if condition else "no")


hdr = ines_hdr()


def readinto(li, struct):
    buf = li.read(sizeof(struct))
    if len(buf) != sizeof(struct):
        return False
    else:
        memmove(addressof(struct), (buf), sizeof(struct))
        return True


def accept_file(li, path):
    """
# ----------------------------------------------------------------------
#
#      check input file format. if recognized, then return 1
#      and fill 'fileformatname'.
#      otherwise return 0
#
"""
    li.seek(0)

    # quit if file is smaller than size of iNes header
    if li.size() < sizeof(ines_hdr):
        return 0

    # set filepos to offset 0
    li.seek(0)

    # read NES header
    assert readinto(li, hdr)

    # is it a valid ROM image in iNes format?
    if(hdr.id != b"NES" or hdr.term != 0x1A):
        return 0

    # this is the name of the file format which will be
    # displayed in IDA's dialog
    fileformatname = "Nintendo Entertainment System ROM"

    return fileformatname


# ----------------------------------------------------------------------
#
#      load file into the database.
#
def load_file(li, _a, _b):
    # set processor to 6502
    if (ph.id != PLFM_6502):
        msg("Nintendo Entertainment System ROM detected: setting processor type to M6502.\n")
        set_processor_type("M6502", SETPROC_LOADER_NON_FATAL)

    try:
        return load_ines_file(li)
    except:
        import traceback
        traceback.print_exc()
        return 0


# ----------------------------------------------------------------------
#
#
def write_file(fp, _):
    warning("[debug-msg] when am I being called?\n")
    return 0


# ----------------------------------------------------------------------
#
#      loads the whole file into IDA
#      this is a wrapper function, which:
#
#      - checks the header for validity and fixes broken headers
#      - creates all necessary segments
#      - saves the whole file to blobs
#      - loads prg pages/banks
#      - adds informational descriptions to the database
#
def load_ines_file(li):
    # go to file offset 0 - just to be sure
    li.seek(0)

    # read the whole header
    if not readinto(li, hdr):
        vloader_failure("File read error!", 0)
        return 0

    # check if header is corrupt
    # show a warning msg, but load the rom nonetheless
    if(hdr.is_corrupt_ines_hdr()):
        # warning("The iNES header seems to be corrupt.\nLoader might give inaccurate results!")
        code = askyn_c(1, "The iNES header seems to be corrupt.\n"
                       "The NES loader could produce wrong results!\n"
                       "Do you want to internally fix the header ?\n\n"
                       "(this will not affect the input file)")
        if(code == 1):
            fix_ines_hdr()

    # create NES segments
    create_segments(li)

    # save NES file to blobs
    save_image_as_blobs(li)

    # load relevant ROM banks into database
    load_rom_banks(li)

    # make vectors public
    add_entry_points(li)

    # fill inf structure
    set_ida_export_data()

    # add information about the ROM image
    describe_rom_image()

    # let IDA add some information about the loaded file
    create_filename_cmt()

    return 1


def create_filename_cmt():
    add_extra_line(inf.min_ea, True, "File Name   : %s" % get_root_filename())
    add_extra_line(inf.min_ea, True, "Format      : %s" % inf.filetype)


# ----------------------------------------------------------------------
#
#      creates all necessary segments and initializes them, if possible
#
def create_segments(li):
    # create RAM segment
    create_ram_segment()

    # create segment for I/O registers
    # NES uses memory mapped I/O
    create_ioreg_segment()

    # create SRAM segment if supported by cartridge
    # if( INES_MASK_SRAM( hdr.rom_control_byte_0 ) )
    create_sram_segment()

    # create segment for expansion ROM
    create_exprom_segment()

    # load trainer, if one is present
    if(INES_MASK_TRAINER(hdr.rom_control_byte_0)):
        warning("This ROM image seems to have a trainer.\n"
                "By default, this loader assumes the trainer to be mapped to $7000.\n")
        load_trainer(li)

    # create segment for PRG ROMs
    create_rom_segment()


# ----------------------------------------------------------------------
#
#      creates an SRAM segment, if available on cartridge
#
def create_sram_segment():
    success = add_segm(0, SRAM_START_ADDRESS,
                       SRAM_START_ADDRESS + SRAM_SIZE, "SRAM", None) == 1
    msg("creating SRAM segment..%s" % ("ok!\n" if success else "failure!\n"))
    if(not success):
        return
    set_segm_addressing(getseg(SRAM_START_ADDRESS), 0)


# ----------------------------------------------------------------------
#
#      creates a RAM segment
#
def create_ram_segment():
    success = add_segm(0, RAM_START_ADDRESS,
                       RAM_START_ADDRESS + RAM_SIZE, "RAM", None) == 1
    msg("creating RAM segment..%s" % ("ok!\n" if success else "failure!\n"))
    if(not success):
        return
    set_segm_addressing(getseg(RAM_START_ADDRESS), 0)

    # how do I properly initialize a segment ?
    # for( unsigned int ea = SRAM_START_ADDRESS; ea<= SRAM_START_ADDRESS + SRAM_SIZE; ea++ )
    #    put_byte( ea, 0 )


# ----------------------------------------------------------------------
#
#      creates an I/O registers segment and names all io registers
#
def create_ioreg_segment():
    success = add_segm(0, IOREGS_START_ADDRESS,
                       IOREGS_START_ADDRESS + IOREGS_SIZE, "IO_REGS", None) == 1
    msg("creating IO_REGS segment..%s" %
        ("ok!\n" if success else "failure!\n"))
    if(not success):
        return
    set_segm_addressing(getseg(IOREGS_START_ADDRESS), 0)

    define_item(PPU_CR_1_ADDRESS, PPU_CR_1_SIZE,
                PPU_CR_1_SHORT_DESCRIPTION, PPU_CR_1_COMMENT)
    define_item(PPU_CR_2_ADDRESS, PPU_CR_2_SIZE,
                PPU_CR_2_SHORT_DESCRIPTION, PPU_CR_2_COMMENT)
    define_item(PPU_SR_ADDRESS, PPU_SR_SIZE,
                PPU_SR_SHORT_DESCRIPTION, PPU_SR_COMMENT)

    define_item(SPR_RAM_AR_ADDRESS, SPR_RAM_AR_SIZE,
                SPR_RAM_AR_SHORT_DESCRIPTION, SPR_RAM_AR_COMMENT)
    define_item(SPR_RAM_IOR_ADDRESS, SPR_RAM_IOR_SIZE,
                SPR_RAM_IOR_SHORT_DESCRIPTION, SPR_RAM_IOR_COMMENT)

    define_item(VRAM_AR_1_ADDRESS, VRAM_AR_1_SIZE,
                VRAM_AR_1_SHORT_DESCRIPTION, VRAM_AR_1_COMMENT)
    define_item(VRAM_AR_2_ADDRESS, VRAM_AR_2_SIZE,
                VRAM_AR_2_SHORT_DESCRIPTION, VRAM_AR_2_COMMENT)
    define_item(VRAM_IOR_ADDRESS, VRAM_IOR_SIZE,
                VRAM_IOR_SHORT_DESCRIPTION, VRAM_IOR_COMMENT)

    define_item(PAPU_PULSE_1_CR_ADDRESS, PAPU_PULSE_1_CR_SIZE,
                PAPU_PULSE_1_CR_SHORT_DESCRIPTION, PAPU_PULSE_1_CR_COMMENT)
    define_item(PAPU_PULSE_1_RCR_ADDRESS, PAPU_PULSE_1_RCR_SIZE,
                PAPU_PULSE_1_RCR_SHORT_DESCRIPTION, PAPU_PULSE_1_RCR_COMMENT)
    define_item(PAPU_PULSE_1_FTR_ADDRESS, PAPU_PULSE_1_FTR_SIZE,
                PAPU_PULSE_1_FTR_SHORT_DESCRIPTION, PAPU_PULSE_1_FTR_COMMENT)
    define_item(PAPU_PULSE_1_CTR_ADDRESS, PAPU_PULSE_1_CTR_SIZE,
                PAPU_PULSE_1_CTR_SHORT_DESCRIPTION, PAPU_PULSE_1_CTR_COMMENT)

    define_item(PAPU_PULSE_2_CR_ADDRESS, PAPU_PULSE_2_CR_SIZE,
                PAPU_PULSE_2_CR_SHORT_DESCRIPTION, PAPU_PULSE_2_CR_COMMENT)
    define_item(PAPU_PULSE_2_RCR_ADDRESS, PAPU_PULSE_2_RCR_SIZE,
                PAPU_PULSE_2_RCR_SHORT_DESCRIPTION, PAPU_PULSE_2_RCR_COMMENT)
    define_item(PAPU_PULSE_2_FTR_ADDRESS, PAPU_PULSE_2_FTR_SIZE,
                PAPU_PULSE_2_FTR_SHORT_DESCRIPTION, PAPU_PULSE_2_FTR_COMMENT)
    define_item(PAPU_PULSE_2_CTR_ADDRESS, PAPU_PULSE_2_CTR_SIZE,
                PAPU_PULSE_2_CTR_SHORT_DESCRIPTION, PAPU_PULSE_2_CTR_COMMENT)

    define_item(PAPU_TRIANGLE_CR_1_ADDRESS, PAPU_TRIANGLE_CR_1_SIZE,
                PAPU_TRIANGLE_CR_1_SHORT_DESCRIPTION, PAPU_TRIANGLE_CR_1_COMMENT)
    define_item(PAPU_TRIANGLE_CR_2_ADDRESS, PAPU_TRIANGLE_CR_2_SIZE,
                PAPU_TRIANGLE_CR_2_SHORT_DESCRIPTION, PAPU_TRIANGLE_CR_2_COMMENT)
    define_item(PAPU_TRIANGLE_FR_1_ADDRESS, PAPU_TRIANGLE_FR_1_SIZE,
                PAPU_TRIANGLE_FR_1_SHORT_DESCRIPTION, PAPU_TRIANGLE_FR_1_COMMENT)
    define_item(PAPU_TRIANGLE_FR_2_ADDRESS, PAPU_TRIANGLE_FR_2_SIZE,
                PAPU_TRIANGLE_FR_2_SHORT_DESCRIPTION, PAPU_TRIANGLE_FR_2_COMMENT)

    define_item(PAPU_NOISE_CR_1_ADDRESS, PAPU_NOISE_CR_1_SIZE,
                PAPU_NOISE_CR_1_SHORT_DESCRIPTION, PAPU_NOISE_CR_1_COMMENT)
    define_item(PAPU_NOISE_CR_2_ADDRESS, PAPU_NOISE_CR_2_SIZE,
                PAPU_NOISE_CR_2_SHORT_DESCRIPTION, PAPU_NOISE_CR_2_COMMENT)
    define_item(PAPU_NOISE_FR_1_ADDRESS, PAPU_NOISE_FR_1_SIZE,
                PAPU_NOISE_FR_1_SHORT_DESCRIPTION, PAPU_NOISE_FR_1_COMMENT)
    define_item(PAPU_NOISE_FR_2_ADDRESS, PAPU_NOISE_FR_2_SIZE,
                PAPU_NOISE_FR_2_SHORT_DESCRIPTION, PAPU_NOISE_FR_2_COMMENT)

    define_item(PAPU_DM_CR_ADDRESS, PAPU_DM_CR_SIZE,
                PAPU_DM_CR_SHORT_DESCRIPTION, PAPU_DM_CR_COMMENT)
    define_item(PAPU_DM_DAR_ADDRESS, PAPU_DM_DAR_SIZE,
                PAPU_DM_DAR_SHORT_DESCRIPTION, PAPU_DM_DAR_COMMENT)
    define_item(PAPU_DM_AR_ADDRESS, PAPU_DM_AR_SIZE,
                PAPU_DM_AR_SHORT_DESCRIPTION, PAPU_DM_AR_COMMENT)
    define_item(PAPU_DM_DLR_ADDRESS, PAPU_DM_DLR_SIZE,
                PAPU_DM_DLR_SHORT_DESCRIPTION, PAPU_DM_DLR_COMMENT)

    define_item(PAPU_SV_CSR_ADDRESS, PAPU_SV_CSR_SIZE,
                PAPU_SV_CSR_SHORT_DESCRIPTION, PAPU_SV_CSR_COMMENT)

    define_item(SPRITE_DMAR_ADDRESS, SPRITE_DMAR_SIZE,
                SPRITE_DMAR_SHORT_DESCRIPTION, SPRITE_DMAR_COMMENT)

    define_item(JOYPAD_1_ADDRESS, JOYPAD_1_SIZE,
                JOYPAD_1_SHORT_DESCRIPTION, JOYPAD_1_COMMENT)
    define_item(JOYPAD_2_ADDRESS, JOYPAD_2_SIZE,
                JOYPAD_2_SHORT_DESCRIPTION, JOYPAD_2_COMMENT)


# ----------------------------------------------------------------------
#
#      creates a ROM segment where all the code is being loaded to
#
def create_rom_segment():
    success = add_segm(0, ROM_START_ADDRESS,
                       ROM_START_ADDRESS + ROM_SIZE, "ROM", "CODE") == 1
    msg("creating ROM segment..%s" % ("ok!\n" if success else "failure!\n"))
    if(not success):
        return
    set_segm_addressing(getseg(ROM_START_ADDRESS), 0)


# ----------------------------------------------------------------------
#
#      creates an EXPANSION ROM segment, I don't know when it is used
#
def create_exprom_segment():
    success = add_segm(0, EXPROM_START_ADDRESS,
                       EXPROM_START_ADDRESS + EXPROM_SIZE, "EXP_ROM", None) == 1
    msg("creating EXP_ROM segment..%s" %
        ("ok!\n" if success else "failure!\n"))
    if(not success):
        return
    set_segm_addressing(getseg(EXPROM_START_ADDRESS), 0)


# ----------------------------------------------------------------------
#
#      loads a 512 byte trainer (located at file offset INES_HDR_SIZE)
#      to TRAINER_START_ADDRESS
#
def load_trainer(li):
    if(not INES_MASK_SRAM(hdr.rom_control_byte_0)):
        success = add_segm(0, TRAINER_START_ADDRESS, TRAINER_START_ADDRESS +
                           TRAINER_SIZE, "TRAINER", "CODE") == 1
        msg("creating TRAINER segment..%s", "ok!\n" if success else "failure!\n")
        set_segm_addressing(getseg(TRAINER_START_ADDRESS), 0)
    li.file2base(INES_HDR_SIZE, TRAINER_START_ADDRESS,
              TRAINER_START_ADDRESS + TRAINER_SIZE, FILEREG_PATCHABLE)


# ----------------------------------------------------------------------
#
#      load 8k chr rom bank into database
#
def load_chr_rom_bank(li, banknr, address):
    # todo: add support for PPU
    # this function currently is disabled, since no
    # segment for the PPU is created
    msg("The loader was trying to load a CHR bank but the PPU is not supported yet.\n")
    return

    if((banknr == 0) or (hdr.chr_page_count_8k == 0)):
        return

    # this is the file offset to begin reading pages from
    offset = INES_HDR_SIZE + \
        (TRAINER_SIZE if INES_MASK_TRAINER(hdr.rom_control_byte_0) else 0) + \
        PRG_PAGE_SIZE * hdr.prg_page_count_16k + \
        (banknr - 1) * CHR_ROM_BANK_SIZE

    # load page from ROM file into segment
    msg("mapping CHR-ROM page %02d to %08x-%08x (file offset %08x) ..",
        banknr, address, address + CHR_PAGE_SIZE, offset)
    if(file2base(li, offset, address, address + CHR_ROM_BANK_SIZE, FILEREG_PATCHABLE) == 1):
        msg("ok\n")
    else:
        msg("failure (corrupt ROM image?)\n")


# ----------------------------------------------------------------------
#
#      load 16k prg rom bank into database
#
def load_prg_rom_bank(li, banknr, address):

    if((banknr == 0) or (hdr.prg_page_count_16k == 0)):
        return

    # this is the file offset to begin reading pages from
    offset = INES_HDR_SIZE + \
        (TRAINER_SIZE if INES_MASK_TRAINER(hdr.rom_control_byte_0) else 0) + \
        (banknr - 1) * PRG_ROM_BANK_SIZE

    # load page from ROM file into segment
    msg("mapping PRG-ROM page %02d to %08x-%08x (file offset %08x) .." %
        (1, address, address + PRG_ROM_BANK_SIZE, offset))
    if(li.file2base(offset, address, address + PRG_ROM_BANK_SIZE, FILEREG_PATCHABLE) == 1):
        msg("ok\n")
    else:
        msg("failure (corrupt ROM image?)\n")


# ----------------------------------------------------------------------
#
#      load 8k prg rom bank into database
#
def load_8k_prg_rom_bank(li, banknr, address):

    if((banknr == 0) or (hdr.prg_page_count_16k == 0)):
        return

    # this is the file offset to begin reading pages from
    offset = INES_HDR_SIZE + \
        (TRAINER_SIZE if INES_MASK_TRAINER(hdr.rom_control_byte_0) else 0) + \
        (banknr - 1) * PRG_ROM_8K_BANK_SIZE

    # load page from ROM file into segment
    msg("mapping 8k PRG-ROM page %02d to %08x-%08x (file offset %08x) ..",
        1, address, address + PRG_ROM_8K_BANK_SIZE, offset)
    if(file2base(li, offset, address, address + PRG_ROM_8K_BANK_SIZE, FILEREG_PATCHABLE) == 1):
        msg("ok\n")
    else:
        msg("failure (corrupt ROM image?)\n")


# ----------------------------------------------------------------------
#
#      this function loads the image into the ida database
#      depending on the mapper in use
#
def load_rom_banks(li):
    mapper = INES_MASK_MAPPER_VERSION(
        hdr.rom_control_byte_0, hdr.rom_control_byte_1)
    if mapper in (MAPPER_NONE,
                  MAPPER_MMC1,
                  MAPPER_UNROM,
                  MAPPER_CNROM,
                  MAPPER_MMC3,
                  MAPPER_MMC5,
                  MAPPER_FFE_F4XXX,
                  MAPPER_MMC4,
                  MAPPER_BANDAI,
                  MAPPER_FFE_F8XXX,
                  MAPPER_JALECO_SS8806,
                  MAPPER_KONAMI_VRC4,
                  MAPPER_KONAMI_VRC2_TYPE_A,
                  MAPPER_KONAMI_VRC2_TYPE_B,
                  MAPPER_KONAMI_VRC6,
                  MAPPER_NAMCOT_106,
                  MAPPER_IREM_G_101,
                  MAPPER_TAITO_TC0190,
                  MAPPER_IREM_H_3001,
                  MAPPER_SUNSOFT_MAPPER_4,
                  MAPPER_SUNSOFT_FME7,  # not sure about this mapper
                  MAPPER_CAMERICA,
                  MAPPER_IREM_74HC161_32,
                  MAPPER_GNROM,
                  ):
        load_prg_rom_bank(li, 1, PRG_ROM_BANK_LOW_ADDRESS)
        load_prg_rom_bank(li, hdr.prg_page_count_16k,
                          PRG_ROM_BANK_HIGH_ADDRESS)
        load_chr_rom_bank(li, 1, CHR_ROM_BANK_ADDRESS)

    elif mapper == MAPPER_HK_SF3:  # last prg, last prg, 1st chr
        load_prg_rom_bank(li, hdr.prg_page_count_16k,
                          PRG_ROM_BANK_LOW_ADDRESS)
        load_prg_rom_bank(li, hdr.prg_page_count_16k,
                          PRG_ROM_BANK_HIGH_ADDRESS)
        load_chr_rom_bank(li, 1, CHR_ROM_BANK_ADDRESS)

    elif mapper in (MAPPER_AOROM,  # 1st prg, 2nd prg, 1st chr
                  MAPPER_FFE_F3XXX,
                  MAPPER_COLOR_DREAMS,
                  MAPPER_100_IN_1,
                  MAPPER_NINA_1):
        load_prg_rom_bank(li, 1, PRG_ROM_BANK_LOW_ADDRESS)
        load_prg_rom_bank(li, 2, PRG_ROM_BANK_HIGH_ADDRESS)
        load_chr_rom_bank(li, 1, CHR_ROM_BANK_ADDRESS)
    elif mapper == MAPPER_MMC2:  # 1st 8k prg, last three 8k prgs, 1st chr
        load_8k_prg_rom_bank(li, 1, PRG_ROM_BANK_LOW_ADDRESS)
        load_8k_prg_rom_bank(li, hdr.prg_page_count_16k *
                             2 - 2, PRG_ROM_BANK_A000)
        load_prg_rom_bank(li, hdr.prg_page_count_16k,
                          PRG_ROM_BANK_HIGH_ADDRESS)
        load_chr_rom_bank(li, 1, CHR_ROM_BANK_ADDRESS)

    elif mapper == MAPPER_TENGEN_RAMBO_1:  # last 8k prg, last 8k prg, last 8k prg, last 8k prg, 1st chr
        load_8k_prg_rom_bank(li, hdr.prg_page_count_16k*2, PRG_ROM_BANK_8000)
        load_8k_prg_rom_bank(li, hdr.prg_page_count_16k*2, PRG_ROM_BANK_A000)
        load_8k_prg_rom_bank(li, hdr.prg_page_count_16k*2, PRG_ROM_BANK_C000)
        load_8k_prg_rom_bank(li, hdr.prg_page_count_16k*2, PRG_ROM_BANK_E000)
        load_chr_rom_bank(li, 1, CHR_ROM_BANK_ADDRESS)
    else:  # 1st prg, last prg, 1st chr
        warning("Mapper %d is not supported by this loader!\n"
                "This could be a corrupt ROM image!\n"
                "Loading first and last PRG-ROM banks by default." % mapper)


# ----------------------------------------------------------------------
#
#      saves prg and chr ROM pages/banks to a binary large object (blob)
#
def save_image_as_blobs(li):
    # store ines header in a blob
    save_ines_hdr_as_blob()

    save_trainer_as_blob(li)

    # store rom image in blobs
    save_prg_rom_pages_as_blobs(li, hdr.prg_page_count_16k)
    save_chr_rom_pages_as_blobs(li, hdr.chr_page_count_8k)


# ----------------------------------------------------------------------
#
#      store header to netnode
#
def save_ines_hdr_as_blob():
    hdr_node = ida_netnode.netnode()

    if(not hdr_node.create(INES_HDR_NODE)):
        return False
    buf = create_string_buffer(INES_HDR_SIZE)
    memmove(buf, addressof(hdr), sizeof(hdr))
    return hdr_node.setblob(buf.raw, 0, 'I')


# ----------------------------------------------------------------------
#
#      store trainer to netnode
#
def save_trainer_as_blob(li):
    node = ida_netnode.netnode()

    if(not INES_MASK_TRAINER(hdr.rom_control_byte_0)):
        return False

    li.seek(INES_HDR_SIZE)
    buffer = li.read(TRAINER_SIZE)
    if(not node.create("$ Trainer")):
        return False
    if(not node.setblob(buffer, TRAINER_SIZE, 0, 'I')):
        msg("Could not store trainer to netnode!\n")

    return True


# ----------------------------------------------------------------------
#
#      store PRG ROM pages to netnode
#
def save_prg_rom_pages_as_blobs(li, count):
    node = ida_netnode.netnode()

    li.seek(TRAINER_SIZE if INES_HDR_SIZE +
            (INES_MASK_TRAINER(hdr.rom_control_byte_0)) else 0)

    for i in range(count):
        buffer = li.read(PRG_PAGE_SIZE)
        prg_node_name = "$ PRG-ROM page %d" % i
        if(not node.create(prg_node_name)):
            return False
        if(not node.setblob(buffer, 0, 'I')):
            msg("Could not store PRG-ROM pages to netnode!\n")

    return True


# ----------------------------------------------------------------------
#
#      store CHR ROM pages to netnode
#
def save_chr_rom_pages_as_blobs(li, count):
    node = ida_netnode.netnode()

    li.seek(INES_HDR_SIZE + (TRAINER_SIZE if INES_MASK_TRAINER(hdr.rom_control_byte_0)
                             else 0) + PRG_PAGE_SIZE * hdr.prg_page_count_16k)

    for i in range(count):
        buffer = li.read(CHR_PAGE_SIZE)
        chr_node_name = "$ CHR-ROM page %d" % i
        if(not node.create(chr_node_name)):
            return False
        if(not node.setblob(buffer, 0, 'I')):
            msg("Could not store CHR-ROM pages to netnode!\n")

    return True


# ----------------------------------------------------------------------
#
#      returns name of mapper
#
def get_mapper_name(mapper):
    if(mapper > MAPPER_LAST):
        return MAPPER_NOT_SUPPORTED
    return mapper_names[mapper]


# ----------------------------------------------------------------------
#
#      add information about the ROM image to disassembly
#
def describe_rom_image():
    mapper = INES_MASK_MAPPER_VERSION(
        hdr.rom_control_byte_0, hdr.rom_control_byte_1)

    add_extra_line(inf.min_ea, True, "\n;   ROM information\n"
                              ";   ---------------\n;")
    add_extra_line(inf.min_ea, True, ";   Valid image header      : %s" % YES_NO(not hdr.is_corrupt_ines_hdr()))
    add_extra_line(inf.min_ea, True, ";   16K PRG-ROM page count  : %d" % hdr.prg_page_count_16k)
    add_extra_line(inf.min_ea, True, ";   8K CHR-ROM page count   : %d" % hdr.chr_page_count_8k)
    add_extra_line(inf.min_ea, True, ";   Mirroring               : %s" % ("horizontal" if INES_MASK_H_MIRRORING(hdr.rom_control_byte_0) else "vertical"))
    add_extra_line(inf.min_ea, True, ";   SRAM enabled            : %s" % YES_NO(INES_MASK_SRAM(hdr.rom_control_byte_0)))
    add_extra_line(inf.min_ea, True, ";   512-byte trainer        : %s" % YES_NO(INES_MASK_TRAINER(hdr.rom_control_byte_0)))
    add_extra_line(inf.min_ea, True, ";   Four screen VRAM layout : %s" % YES_NO(INES_MASK_VRAM_LAYOUT(hdr.rom_control_byte_0)))
    add_extra_line(inf.min_ea, True, ";   Mapper                  : %s (Mapper #%d)" % (get_mapper_name(mapper), mapper))


# ----------------------------------------------------------------------
#
#      defines, names and comments an item
#
def define_item(address, size, shortdesc, comment):
    del_items(address, True)
    create_data(address, (word_flag() if size ==
                          IOREG_16 else byte_flag()), size, ida_netnode.BADNODE)
    set_name(address, shortdesc)
    set_cmt(address, comment, True)


# ----------------------------------------------------------------------
#
#      gets a vector's address
#      vec either is one of the following constants:
#
#      #define NMI_VECTOR_START_ADDRESS            0xFFFA
#      #define RESET_VECTOR_START_ADDRESS          0xFFFC
#      #define IRQ_VECTOR_START_ADDRESS            0xFFFE
#
def get_vector(vec):
    return get_word(vec)


# ----------------------------------------------------------------------
#
#      define location as word (2 byte), convert it to an offset, rename it
#      and comment it with the file offset
#
def name_vector(address, name):
    del_items(address, True)
    create_data(address, word_flag(), 2, ida_netnode.BADNODE)
    op_offset(address, 0, 0)
    set_name(address, name)


# ----------------------------------------------------------------------
#
#      add entrypoints to the database and name vectors
#
def add_entry_points(li):
    ea = get_vector(NMI_VECTOR_START_ADDRESS)
    add_entry(ea, ea, "NMI_routine", True)
    name_vector(NMI_VECTOR_START_ADDRESS, "NMI_vector")

    ea = get_vector(RESET_VECTOR_START_ADDRESS)
    add_entry(ea, ea, "RESET_routine", True)
    name_vector(RESET_VECTOR_START_ADDRESS, "RESET_vector")

    ea = get_vector(IRQ_VECTOR_START_ADDRESS)
    add_entry(ea, ea, "IRQ_routine", True)
    name_vector(IRQ_VECTOR_START_ADDRESS, "IRQ_vector")

    return True


# ----------------------------------------------------------------------
#
#      set entrypoint, min_ea, maxEA, start_cs and filetype
#
def set_ida_export_data():

    # set entrypoint
    inf.start_ip = inf.begin_ea = get_vector(RESET_VECTOR_START_ADDRESS)

    # set min_ea, maxEA, etc.
    inf.start_cs = 0
    inf.min_ea = RAM_START_ADDRESS
    inf.max_ea = ROM_START_ADDRESS + ROM_SIZE
