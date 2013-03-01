#Group 1: Arithmetic
OP_ADD = 0x00
OP_SUB = 0x01
OP_MUL = 0x02
OP_DIV = 0x03
OP_MOD = 0x04

#Group 2: Binary
OP_OR  = 0x10
OP_XOR = 0x11
OP_AND = 0x12
OP_NOT = 0x13
OP_SHL = 0x14
OP_SHR = 0x15

#Group 3: Misc
OP_MOV = 0x20
OP_NOP = 0x21
OP_HALT= 0x22
OP_PRINT=0x23

#Group 4: Compare
OP_CMP = 0x30

#Group 5: Branches
OP_JMP = 0x40
OP_JZ  = 0x41
OP_JNZ = 0x42
OP_JGT = 0x43
OP_JGE = 0x44
OP_CALL= 0x45
OP_RET = 0x46

#Group 6: Stack
OP_PUSH= 0x50
OP_POP = 0x51

#Group 7: Interrupts
OP_INT = 0x60
OP_RETI= 0x61
OP_VMRESUME=0x62


#Special Registers
SPECIALREG_SEGTBL	=	0
SPECIALREG_VMTBL	=	1
SPECIALREG_CS		=	2
SPECIALREG_DS		=	3
SPECIALREG_ES		=	4
SPECIALREG_RS		=	5
SPECIALREG_SS		=	6

SPECIALREGS = {
	'segtbl': SPECIALREG_SEGTBL,
	'vmtbl': SPECIALREG_VMTBL,
	'cs': SPECIALREG_CS,
	'ds': SPECIALREG_DS,
	'es': SPECIALREG_ES,
	'rs': SPECIALREG_RS,
	'ss': SPECIALREG_SS
}

SPECIALREGS_NAMES = [
	'SEGTBL',
	'VMTBL',
	'CS',
	'DS',
	'ES',
	'RS',
	'SS'
]


#Possible parameter types
PARAM_IMMEDIATE 		= 0x00
PARAM_REGISTER			= 0x01
PARAM_MEMORY_SINGLE_DS 	= 0x02
PARAM_MEMORY_SINGLE_ES	= 0x03
PARAM_MEMORY_DOUBLE_DS	= 0x04
PARAM_MEMORY_DOUBLE_ES	= 0x05
PARAM_SPECIAL_REGISTER	= 0x06

#Possible segment types
SEGMENT_CODE			= 0x00
SEGMENT_DATA			= 0x01
SEGMENT_REGISTER		= 0x02
SEGMENT_STACK			= 0x03
SEGMENT_TYPES = [SEGMENT_CODE, SEGMENT_DATA, SEGMENT_REGISTER, SEGMENT_STACK]
SEGMENTTYPE_NAMES = [
	'Code',
	'Data',
	'Register',
	'Stack'
]

#Possible interrupts
INTR_RESET = 0
INTR_SEG_VIOL = 1
INTR_INVALID_INSTR = 2
INTR_DIV_BY_ZERO = 3
INTR_HV_TRAP = 4
INTR_TIMER = 5
INTR_SOFTWARE = 6

#Possible reasons for Hypervisor traps
HVTRAP_SEG_VIOL = 0
HVTRAP_INVALID_INSTR = 1
HVTRAP_DIV_BY_ZERO = 2
HVTRAP_HVTRAP = 3
HVTRAP_SOFTWARE = 4
HVTRAP_PRIVILEGE_VIOL = 5
HVTRAP_SPECIAL_REG_READ = 6
HVTRAP_SPECIAL_REG_WRITE = 7
HVTRAP_HALT = 8
HVTRAP_HARDWARE_ACCESS = 9
HVTRAP_VMRESUME = 10

#Conversion from real interrupts to hypervisor traps
INTR_TO_HVTRAP = {
	INTR_SEG_VIOL: HVTRAP_SEG_VIOL,
	INTR_INVALID_INSTR: HVTRAP_INVALID_INSTR,
	INTR_DIV_BY_ZERO: HVTRAP_DIV_BY_ZERO,
	INTR_HV_TRAP: HVTRAP_HVTRAP,
	INTR_SOFTWARE: HVTRAP_SOFTWARE
}
