"""

	Nintendo Entertainment System (NES) loader module
	------------------------------------------------------
	Copyright 2006, Dennis Elser (dennis@backtrace.de)

"""

# size of 8 and 16 bit I/O registers
IOREG_8 = 1
IOREG_16 = 2

# Picture Processing Unit I/O regs
PPU_CR_1_ADDRESS = 0x2000
PPU_CR_1_SIZE = IOREG_8
PPU_CR_1_SHORT_DESCRIPTION = "PPU_CR_1"
PPU_CR_1_COMMENT = "PPU Control Register #1 (W)\n\n" \
                                            "   D7: Execute NMI on VBlank\n" \
                                            "   D6: PPU Master/Slave Selection\n" \
                                            "   D5: Sprite Size\n" \
                                            "   D4: Background Pattern Table Address\n" \
                                            "   D3: Sprite Pattern Table Address\n" \
                                            "   D2: PPU Address Increment\n" \
                                            "D1-D0: Name Table Address"

PPU_CR_2_ADDRESS = 0x2001
PPU_CR_2_SIZE = IOREG_8
PPU_CR_2_SHORT_DESCRIPTION = "PPU_CR_2"
PPU_CR_2_COMMENT = "PPU Control Register #2 (W)\n\n" \
                                            "D7-D5: Full Background Colour (when D0 == 1)\n" \
                                            "D7-D5: Colour Intensity (when D0 == 0)\n" \
                                            "   D4: Sprite Visibility\n" \
                                            "   D3: Background Visibility\n" \
                                            "   D2: Sprite Clipping\n" \
                                            "   D1: Background Clipping\n" \
                                            "   D0: Display Type"

PPU_SR_ADDRESS = 0x2002
PPU_SR_SIZE = IOREG_8
PPU_SR_SHORT_DESCRIPTION = "PPU_SR"
PPU_SR_COMMENT = "PPU Status Register (R)\n\n" \
                                            "   D7: VBlank Occurance\n" \
                                            "   D6: Sprite #0 Occurance\n" \
                                            "   D5: Scanline Sprite Count\n" \
                                            "   D4: VRAM Write Flag\n\n" \
                                            "" \
                                            "NOTE: D7 is set to 0 after read occurs.\n" \
                                            "NOTE: After a read occurs, $2005 is reset, hence the\n" \
                                            "      next write to $2005 will be Horizontal.\n" \
                                            "NOTE: After a read occurs, $2006 is reset, hence the\n" \
                                            "      next write to $2006 will be the high byte portion."

# Sprite RAM I/O regs
SPR_RAM_AR_ADDRESS = 0x2003
SPR_RAM_AR_SIZE = IOREG_8
SPR_RAM_AR_SHORT_DESCRIPTION = "SPR_RAM_AR"
SPR_RAM_AR_COMMENT = "SPR-RAM Address Register (W)\n\n" \
                                            "D7-D0: 8-bit address in SPR-RAM to access via $2004."

SPR_RAM_IOR_ADDRESS = 0x2004
SPR_RAM_IOR_SIZE = IOREG_8
SPR_RAM_IOR_SHORT_DESCRIPTION = "SPR_RAM_IOR"
SPR_RAM_IOR_COMMENT = "SPR-RAM I/O Register (W)\n\n" \
                                            "D7-D0: 8-bit data written to SPR-RAM."

# VRAM I/O regs
VRAM_AR_1_ADDRESS = 0x2005
VRAM_AR_1_SIZE = IOREG_8
VRAM_AR_1_SHORT_DESCRIPTION = "VRAM_AR_1"
VRAM_AR_1_COMMENT = "VRAM Address Register #1 (W2)\n\n" \
                                            "Commonly used used to \"pan/scroll\" the screen (sprites\n" \
                                            "excluded) horizontally and vertically. However, there\n" \
                                            "is no actual panning hardware inside the NES. This\n" \
                                            "register controls VRAM addressing lines."

VRAM_AR_2_ADDRESS = 0x2006
VRAM_AR_2_SIZE = IOREG_8
VRAM_AR_2_SHORT_DESCRIPTION = "VRAM_AR_2"
VRAM_AR_2_COMMENT = "VRAM Address Register #2 (W2)\n\n" \
                                            "Commonly used to specify the 16-bit address in VRAM to\n" \
                                            "access via $2007. However, this register controls VRAM\n" \
                                            "addressing bits, and therefore should be used with\n" \
                                            "knowledge of how it works, and when it works."


VRAM_IOR_ADDRESS = 0x2007
VRAM_IOR_SIZE = IOREG_8
VRAM_IOR_SHORT_DESCRIPTION = "VRAM_IOR"
VRAM_IOR_COMMENT = "VRAM I/O Register (RW)\n\n" \
                                            "D7-D0: 8-bit data read/written from/to VRAM."

# Pseudo Audio Processing Unit I/O regs

# pulse 1
PAPU_PULSE_1_CR_ADDRESS = 0x4000
PAPU_PULSE_1_CR_SIZE = IOREG_8
PAPU_PULSE_1_CR_SHORT_DESCRIPTION = "pAPU_P_1_CR"
PAPU_PULSE_1_CR_COMMENT = "pAPU Pulse #1 Control Register (W)"
                                            
PAPU_PULSE_1_RCR_ADDRESS = 0x4001
PAPU_PULSE_1_RCR_SIZE = IOREG_8
PAPU_PULSE_1_RCR_SHORT_DESCRIPTION = "pAPU_P_1_RCR"
PAPU_PULSE_1_RCR_COMMENT = "pAPU Pulse #1 Ramp Control Register (W)"
                                            
PAPU_PULSE_1_FTR_ADDRESS = 0x4002
PAPU_PULSE_1_FTR_SIZE = IOREG_8
PAPU_PULSE_1_FTR_SHORT_DESCRIPTION = "pAPU_P_1_FTR"
PAPU_PULSE_1_FTR_COMMENT = "pAPU Pulse #1 Fine Tune (FT) Register (W)"
                                            
PAPU_PULSE_1_CTR_ADDRESS = 0x4003
PAPU_PULSE_1_CTR_SIZE = IOREG_8
PAPU_PULSE_1_CTR_SHORT_DESCRIPTION = "pAPU_P_1_CTR"
PAPU_PULSE_1_CTR_COMMENT = "pAPU Pulse #1 Coarse Tune (CT) Register (W)"


# pulse 2
PAPU_PULSE_2_CR_ADDRESS = 0x4004
PAPU_PULSE_2_CR_SIZE = IOREG_8
PAPU_PULSE_2_CR_SHORT_DESCRIPTION = "pAPU_P_2_CR"
PAPU_PULSE_2_CR_COMMENT = "pAPU Pulse #2 Control Register (W)"
                                            
PAPU_PULSE_2_RCR_ADDRESS = 0x4005
PAPU_PULSE_2_RCR_SIZE = IOREG_8
PAPU_PULSE_2_RCR_SHORT_DESCRIPTION = "pAPU_P_2_RCR"
PAPU_PULSE_2_RCR_COMMENT = "pAPU Pulse #2 Ramp Control Register (W)"
                                            
PAPU_PULSE_2_FTR_ADDRESS = 0x4006
PAPU_PULSE_2_FTR_SIZE = IOREG_8
PAPU_PULSE_2_FTR_SHORT_DESCRIPTION = "pAPU_P_2_FTR"
PAPU_PULSE_2_FTR_COMMENT = "pAPU Pulse #2 Fine Tune (FT) Register (W)"
                                            
PAPU_PULSE_2_CTR_ADDRESS = 0x4007
PAPU_PULSE_2_CTR_SIZE = IOREG_8
PAPU_PULSE_2_CTR_SHORT_DESCRIPTION = "pAPU_P_2_CTR"
PAPU_PULSE_2_CTR_COMMENT = "pAPU Pulse #2 Coarse Tune (CT) Register (W)"


# triangle
PAPU_TRIANGLE_CR_1_ADDRESS = 0x4008
PAPU_TRIANGLE_CR_1_SIZE = IOREG_8
PAPU_TRIANGLE_CR_1_SHORT_DESCRIPTION = "pAPU_T_CR_1"
PAPU_TRIANGLE_CR_1_COMMENT = "pAPU Triangle Control Register #1 (W)"

PAPU_TRIANGLE_CR_2_ADDRESS = 0x4009
PAPU_TRIANGLE_CR_2_SIZE = IOREG_8
PAPU_TRIANGLE_CR_2_SHORT_DESCRIPTION = "pAPU_T_CR_2"
PAPU_TRIANGLE_CR_2_COMMENT = "pAPU Triangle Control Register #2 (?)"

PAPU_TRIANGLE_FR_1_ADDRESS = 0x400A
PAPU_TRIANGLE_FR_1_SIZE = IOREG_8
PAPU_TRIANGLE_FR_1_SHORT_DESCRIPTION = "pAPU_T_FR_1"
PAPU_TRIANGLE_FR_1_COMMENT = "pAPU Triangle Frequency Register #1 (W)"

PAPU_TRIANGLE_FR_2_ADDRESS = 0x400B
PAPU_TRIANGLE_FR_2_SIZE = IOREG_8
PAPU_TRIANGLE_FR_2_SHORT_DESCRIPTION = "pAPU_T_FR_2"
PAPU_TRIANGLE_FR_2_COMMENT = "pAPU Triangle Frequency Register #2 (W)"


# noise
PAPU_NOISE_CR_1_ADDRESS = 0x400C
PAPU_NOISE_CR_1_SIZE = IOREG_8
PAPU_NOISE_CR_1_SHORT_DESCRIPTION = "pAPU_N_CR_1"
PAPU_NOISE_CR_1_COMMENT = "pAPU Noise Control Register #1 (W)"

PAPU_NOISE_CR_2_ADDRESS = 0x400D
PAPU_NOISE_CR_2_SIZE = IOREG_8
PAPU_NOISE_CR_2_SHORT_DESCRIPTION = "Unused" #"pAPU_N_CR_2"
PAPU_NOISE_CR_2_COMMENT = "Unused Noise Control Register #2 ???" #"pAPU Noise Control Register #1 (W)"

PAPU_NOISE_FR_1_ADDRESS = 0x400E
PAPU_NOISE_FR_1_SIZE = IOREG_8
PAPU_NOISE_FR_1_SHORT_DESCRIPTION = "pAPU_N_FR_1"
PAPU_NOISE_FR_1_COMMENT = "pAPU Noise Frequency Register #1 (W)"

PAPU_NOISE_FR_2_ADDRESS = 0x400F
PAPU_NOISE_FR_2_SIZE = IOREG_8
PAPU_NOISE_FR_2_SHORT_DESCRIPTION = "pAPU_N_FR_2"
PAPU_NOISE_FR_2_COMMENT = "pAPU Noise Frequency Register #2 (W)"


# delta modulation
PAPU_DM_CR_ADDRESS = 0x4010
PAPU_DM_CR_SIZE = IOREG_8
PAPU_DM_CR_SHORT_DESCRIPTION = "pAPU_DM_CR"
PAPU_DM_CR_COMMENT = "pAPU Delta Modulation Control Register (W)"

PAPU_DM_DAR_ADDRESS = 0x4011
PAPU_DM_DAR_SIZE = IOREG_8
PAPU_DM_DAR_SHORT_DESCRIPTION = "pAPU_DM_DAR"
PAPU_DM_DAR_COMMENT = "pAPU Delta Modulation D/A Register (W)"

PAPU_DM_AR_ADDRESS = 0x4012
PAPU_DM_AR_SIZE = IOREG_8
PAPU_DM_AR_SHORT_DESCRIPTION = "pAPU_DM_AR"
PAPU_DM_AR_COMMENT = "pAPU Delta Modulation Address Register (W)"

PAPU_DM_DLR_ADDRESS = 0x4013
PAPU_DM_DLR_SIZE = IOREG_8
PAPU_DM_DLR_SHORT_DESCRIPTION = "pAPU_DM_DLR"
PAPU_DM_DLR_COMMENT = "pAPU Delta Modulation Data Length Register (W)"


# Clock Signal / Channel Control
PAPU_SV_CSR_ADDRESS = 0x4015
PAPU_SV_CSR_SIZE = IOREG_8
PAPU_SV_CSR_SHORT_DESCRIPTION = "pAPU_SV_CSR"
PAPU_SV_CSR_COMMENT = "pAPU Sound/Vertical Clock Signal Register (R)\n\n" \
                                             "   D6: Vertical Clock Signal IRQ Availability\n" \
                                             "   D4: Delta Modulation\n" \
                                             "   D3: Noise\n" \
                                             "   D2: Triangle\n" \
                                             "   D1: Pulse #2\n" \
                                             "   D0: Pulse #1\n" \
                                             "---------------------------------------------\n" \
                                             "pAPU Channel Control (W)\n\n" \
                                             "   D4: Delta Modulation\n" \
                                             "   D3: Noise\n" \
                                             "   D2: Triangle\n" \
                                             "   D1: Pulse #2\n" \
                                             "   D0: Pulse #1"




# Sprite DMA I/O regs

SPRITE_DMAR_ADDRESS = 0x4014
SPRITE_DMAR_SIZE = IOREG_8
SPRITE_DMAR_SHORT_DESCRIPTION = "SPRITE_DMAR"
SPRITE_DMAR_COMMENT = "Sprite DMA Register (W)\n\n" \
                                             "Transfers 256 bytes of memory into SPR-RAM. The address\n" \
                                             "read from is $100*N, where N is the value written."


# Joypad I/O regs

JOYPAD_1_ADDRESS = 0x4016
JOYPAD_1_SIZE = IOREG_8
JOYPAD_1_SHORT_DESCRIPTION = "Joypad_1"
JOYPAD_1_COMMENT = "Joypad #1 (RW)\n\n" \
                                             "READING:\n" \
                                             "   D4: Zapper Trigger\n" \
                                             "   D3: Zapper Sprite Detection\n" \
                                             "   D0: Joypad Data\n" \
                                             "----------------------------------------------\n" \
                                             "WRITING:\n" \
                                             "Joypad Strobe (W)\n\n" \
                                             "" \
                                             "   D0: Joypad Strobe\n" \
                                             "----------------------------------------------\n" \
                                             "WRITING:\n" \
                                             "Expansion Port Latch (W)\n" \
                                             "   D0: Expansion Port Method\n"

JOYPAD_2_ADDRESS = 0x4017
JOYPAD_2_SIZE = IOREG_8
JOYPAD_2_SHORT_DESCRIPTION = "Joypad_2"
JOYPAD_2_COMMENT = "Joypad #2/SOFTCLK (RW)\n\n" \
                                             "READING:\n" \
                                             "   D7: Vertical Clock Signal (External)\n" \
                                             "   D6: Vertical Clock Signal (Internal)\n" \
                                             "   D4: Zapper Trigger\n" \
                                             "   D3: Zapper Sprite Detection\n" \
                                             "   D0: Joypad Data\n" \
                                             "----------------------------------------------\n" \
                                             "WRITING:\n" \
                                             "Expansion Port Latch (W)\n\n" \
                                             "" \
                                             "   D0: Expansion Port Method\n"