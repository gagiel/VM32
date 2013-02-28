import struct

from common.Opcodes import *
from Parser import Number, Id, String, MemRef, DoubleMemRef, Instruction, Directive, LabelDef, Register, SpecialRegister
from Exceptions import InstructionError

from ObjectFile import ImportEntry, RelocEntry

class AssembledInstruction(object):
	def __init__(self, op=None, arguments=None):
		self.op = op
		self.arguments = arguments

	def __repr__(self):
		str = "AssembledInstruction: \n"
		str += "\tOp: %s\n" % self.op
		str += "\tArgs: %s\n" % self.arguments
		return str

_INSTR = {
	'add': {
		'nargs': 2,
		'op': OP_ADD,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'sub': {
		'nargs': 2,
		'op': OP_SUB,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'mul': {
		'nargs': 2,
		'op': OP_MUL,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'div': {
		'nargs': 2,
		'op': OP_DIV,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'mod': {
		'nargs': 2,
		'op': OP_MOD,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},

	'or': {
		'nargs': 2,
		'op': OP_OR,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'xor': {
		'nargs': 2,
		'op': OP_XOR,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'and': {
		'nargs': 2,
		'op': OP_AND,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'not': {
		'nargs': 2,
		'op': OP_NOT,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'shl': {
		'nargs': 2,
		'op': OP_SHL,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},
	'shr': {
		'nargs': 2,
		'op': OP_SHR,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Id, Register, Number, MemRef, DoubleMemRef],
		]
	},

	'mov': {
		'nargs': 2,
		'op': OP_MOV,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef, SpecialRegister],
			[Id, Register, Number, MemRef, DoubleMemRef, SpecialRegister],
		]
	},

	'nop': {
		'nargs': 0,
		'op': OP_NOP,
		'paramtypes': []
	},
	'halt': {
		'nargs': 0,
		'op': OP_HALT,
		'paramtypes': []
	},


	'print': {
		'nargs': 1,
		'op': OP_PRINT,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef]
		]
	},


	'cmp': {
		'nargs': 2,
		'op': OP_CMP,
		'paramtypes': [
			[Register, MemRef, DoubleMemRef],
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},


	'jmp': {
		'nargs': 1,
		'op': OP_JMP,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef]
		]
	},
	'jz': {
		'nargs': 1,
		'op': OP_JZ,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},
	'jnz': {
		'nargs': 1,
		'op': OP_JNZ,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},
	'jgt': {
		'nargs': 1,
		'op': OP_JGT,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},
	'jge': {
		'nargs': 1,
		'op': OP_JGE,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},
	'call': {
		'nargs': 1,
		'op': OP_CALL,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},
	'ret': {
		'nargs': 0,
		'op': OP_RET,
		'paramtypes': []
	},

	'push': {
		'nargs': 1,
		'op': OP_PUSH,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},
	'pop': {
		'nargs': 1,
		'op': OP_POP,
		'paramtypes': [
			[Register, Id, Number, MemRef, DoubleMemRef],
		]
	},


	'int': {
		'nargs': 1,
		'op': OP_INT,
		'paramtypes': [
			[Number],
		]
	},


	'reti': {
		'nargs': 0,
		'op': OP_RETI,
		'paramtypes': []
	},
	'vmresume': {
		'nargs': 1,
		'op': OP_VMRESUME,
		'paramtypes': [
			[Number]
		]
	},
}

def doesInstructionExist(instruction):
	return instruction in _INSTR

def getInstructionLength(instruction, args):
	_validateInstruction(instruction, args)

	arglen = 0
	for arg in args:
		#check if we need an extra word for an argument after the opcode
		if isinstance(arg, Id) or isinstance(arg, Number) or isinstance(arg, MemRef) or isinstance(arg, DoubleMemRef):
			arglen += 1

	return 1 + arglen

def _validateInstruction(name, args):
	if not doesInstructionExist(name):
		raise InstructionError("Unknown instruction %s" % name)

	instr = _INSTR[name]

	if len(args) != instr['nargs']:
		raise InstructionError("Instruction %s expected %d arguments, got %d" % (name, instr['nargs'], len(args)))

	for i, arg in enumerate(args):
		if not type(arg) in instr['paramtypes'][i]:
			raise InstructionError("Unexpected argument for instruction %s at position %d of type %s" % (name, i+1, arg.__class__.__name__))

def assembleInstruction(name, args, addr, symtab, defines, privilegeLevel):
	""" Assembles an instruction

		name:
			The instruction in ascii form

		args:
			A list of arguments for this instruction

		addr:
			A desired address where this instruction will be placed at

		symtab:
			The symbol table

		defines:
			Defined constants

		privilegeLevel:
			The privilege level of this instruction
	"""
	_validateInstruction(name, args)

	instr = _INSTR[name]
	
	operandValues = []
	operandTypes = []

	#parse all arguments the instruction needs and gather the operand type, value, import and relocation information
	arguments = []
	i = 1
	for n in range(instr['nargs']):
		(operandType, operandValue, importedSymbol, relocation) = _parseAgumentType(args[n], symtab, defines)
		operandTypes.append(operandType)
		
		if operandValue != None:
			operandValues.append(operandValue)

			#add meta information to instruction if there is any
			if relocation != None or importedSymbol != None:
				arguments.append(
					{
						"offsetInInstruction": i,
						"relocation": relocation,
						"import": importedSymbol
					}
				)

			i += 1

	#create the instruction and operand sequence based on the number of arguments
	if len(operandTypes) == 0:
		operandTypes.extend([0, 0])
	elif len(operandTypes) == 1:
		operandTypes.append(0)

	assert len(operandTypes) == 2, "len(operandTypes) is not 2"
	
	assembled = [
		struct.pack("<BBBB", instr["op"], privilegeLevel, operandTypes[0], operandTypes[1])
	]

	#append argument values
	assembled.extend(map(lambda x: struct.pack("<I", x), operandValues))

	#put everything into a container object and return it for further processing
	#return AssembledInstruction(op=assembled, import_req=importedSymbols, reloc_req=relocations)
	return AssembledInstruction(op=assembled, arguments=arguments)

def _parseAgumentType(arg, symtab, deftab):
	#The argument is a symbolic name
	if isinstance(arg, Register):
		if arg.reg > 30:
			raise InstructionError("Invalid register 'r%s'" % arg.reg)

		return (PARAM_REGISTER << 5 | arg.reg, None, None, None)

	if isinstance(arg, SpecialRegister):
		if not arg.reg in SPECIALREGS:
			raise InstructionError("Invalid special register '%s'" % arg.reg)

		return (PARAM_SPECIAL_REGISTER << 5 | SPECIALREGS[arg.reg], None, None, None)

	if isinstance(arg, Id):
		#check if labelname of the MemRef is a define
		#if so, take it, and return, otherwise check for symbols or import it
		if deftab.has_key(arg.id):
			return (PARAM_IMMEDIATE << 5, deftab[arg.id], None, None)

		#check if labelname of the MemRef is locally defined
		#if it is, then we don't have an external symbol, but a relocation
		#otherwise we have an import
		if arg.id in symtab:
			return (PARAM_IMMEDIATE << 5, symtab[arg.id].offset, None, symtab[arg.id].segment)
		else:
			return (PARAM_IMMEDIATE << 5, 0, arg.id, None)

	#The argument is a number
	elif isinstance(arg, Number):
		if arg.val < 0 or arg.val > 0xFFFFFFFF:
			raise InstructionError("Number must be between 0 and 0xFFFFFFFF")

		return (PARAM_IMMEDIATE << 5, arg.val, None, None)

	#The argument is a memory reference
	elif isinstance(arg, MemRef):
		#Get register offset for memory reference operation
		#register 31 is zero-register
		regOffset = 31
		if arg.offset != None:
			if arg.offset.reg > 30:
				raise InstructionError("Invalid register 'r%s'" % arg.offset.reg)

			regOffset = arg.offset.reg

		#if memory address is a number, handle this here
		if isinstance(arg.id, Number):
			if arg.segment == 'ds':
				return (PARAM_MEMORY_SINGLE_DS << 5 | regOffset, arg.id.val, None, None)
			elif arg.segment == 'es':
				return (PARAM_MEMORY_SINGLE_ES << 5 | regOffset, arg.id.val, None, None)
			else:
				raise Exception("Unknown memory segment: %s" % arg.segment)

		#check if operand is a define
		#if so, take it, and return, otherwise check for local symbols and registers or import it
		if deftab.has_key(arg.id.id):
			if arg.segment == 'ds':
				return (PARAM_MEMORY_SINGLE_DS << 5 | regOffset, deftab[arg.id.id], None, None)
			elif arg.segment == 'es':
				return (PARAM_MEMORY_SINGLE_ES << 5 | regOffset, deftab[arg.id.id], None, None)
			else:
				raise Exception("Unknown memory segment: %s" % arg.segment)

		#check if labelname of the MemRef is locally defined
		#if it is, then we don't have an external symbol, but a relocation
		#otherwise we have an import
		if arg.id.id in symtab:
			offset = symtab[arg.id.id].offset
			externdefinedSymbol = None
			relocation = symtab[arg.id.id].segment
		else:
			offset = 0
			externdefinedSymbol = arg.id.id
			relocation = None

		#create the operand information based on which cpu memory segment is selected
		if arg.segment == 'ds':
			return (PARAM_MEMORY_SINGLE_DS << 5 | regOffset, offset, externdefinedSymbol, relocation)
		elif arg.segment == 'es':
			return (PARAM_MEMORY_SINGLE_ES << 5 | regOffset, offset, externdefinedSymbol, relocation)
		else:
			raise Exception("Unknown memory segment: %s" % arg.segment)

	#The argument is a double memory reference
	elif isinstance(arg, DoubleMemRef):
		#Get register offset for memory reference operation
		#register 31 is zero-register
		regOffset = 31
		if arg.offset != None:
			if arg.offset.reg > 30:
				raise InstructionError("Invalid register 'r%s'" % arg.offset.reg)

			regOffset = arg.offset.reg

		#if memory address is a number, handle this here
		if isinstance(arg.id, Number):
			if arg.segment == 'ds':
				return (PARAM_MEMORY_DOUBLE_DS << 5 | regOffset, arg.id.val, None, None)
			elif arg.segment == 'es':
				return (PARAM_MEMORY_DOUBLE_ES << 5 | regOffset, arg.id.val, None, None)
			else:
				raise Exception("Unknown memory segment: %s" % arg.segment)

		#check if operand is a define
		#if so, take it, and return, otherwise check for local symbols and registers or import it
		if deftab.has_key(arg.id.id):
			if arg.segment == 'ds':
				return (PARAM_MEMORY_DOUBLE_DS << 5 | regOffset, deftab[arg.id.id], None, None)
			elif arg.segment == 'es':
				return (PARAM_MEMORY_DOUBLE_ES << 5 | regOffset, deftab[arg.id.id], None, None)
			else:
				raise Exception("Unknown memory segment: %s" % arg.segment)

		#check if labelname of the MemRef is locally defined
		#if it is, then we don't have an external symbol, but a relocation
		#otherwise we have an import
		if arg.id.id in symtab:
			offset = symtab[arg.id.id].offset
			externdefinedSymbol = None
			relocation = symtab[arg.id.id].segment
		else:
			offset = 0
			externdefinedSymbol = arg.id.id
			relocation = None

		#create the operand information based on which cpu memory segment is selected
		if arg.segment == 'ds':
			return (PARAM_MEMORY_DOUBLE_DS << 5 | regOffset, offset, externdefinedSymbol, relocation)
		elif arg.segment == 'es':
			return (PARAM_MEMORY_DOUBLE_ES << 5 | regOffset, offset, externdefinedSymbol, relocation)
		else:
			raise Exception("Unknown memory segment: %s" % arg.segment)

	else:
		raise InstructionError("Instruction got unknown argument type. Got '%s'" % arg.__class__.__name__)
