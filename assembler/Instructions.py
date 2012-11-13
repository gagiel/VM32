import struct

from common.Opcodes import *
from Parser import Number, Id, String, MemRef, DoubleMemRef, Instruction, Directive, LabelDef
from Exceptions import InstructionError

from ObjectFile import ImportEntry, RelocEntry

class AssembledInstruction(object):
	def __init__(self, op=None, import_req=None, reloc_req=None):
		self.op = op
		self.import_req = import_req
		self.reloc_req = reloc_req

_INSTR = {
	'add': {
		'nargs': 2,
		'op': OP_ADD,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'sub': {
		'nargs': 2,
		'op': OP_SUB,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'mul': {
		'nargs': 2,
		'op': OP_MUL,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'div': {
		'nargs': 2,
		'op': OP_DIV,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'mod': {
		'nargs': 2,
		'op': OP_MOD,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},

	'or': {
		'nargs': 2,
		'op': OP_OR,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'xor': {
		'nargs': 2,
		'op': OP_XOR,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'and': {
		'nargs': 2,
		'op': OP_AND,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'not': {
		'nargs': 2,
		'op': OP_NOT,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},

	'mov': {
		'nargs': 2,
		'op': OP_MOV,
		'paramtypes': [
			[MemRef, DoubleMemRef, PARAM_SPECIAL_REGISTER],
			[Id, Number, MemRef, DoubleMemRef, PARAM_SPECIAL_REGISTER],
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
			[Id, Number, MemRef, DoubleMemRef]
		]
	},


	'cmp': {
		'nargs': 2,
		'op': OP_CMP,
		'paramtypes': [
			[MemRef, DoubleMemRef],
			[Id, Number, MemRef, DoubleMemRef],
		]
	},


	'jmp': {
		'nargs': 1,
		'op': OP_JMP,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef]
		]
	},
	'jz': {
		'nargs': 1,
		'op': OP_JZ,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'jnz': {
		'nargs': 1,
		'op': OP_JNZ,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'jgt': {
		'nargs': 1,
		'op': OP_JGT,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'call': {
		'nargs': 1,
		'op': OP_CALL,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'ret': {
		'nargs': 0,
		'op': OP_RET,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
		]
	},

	'push': {
		'nargs': 1,
		'op': OP_PUSH,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
		]
	},
	'pop': {
		'nargs': 1,
		'op': OP_POP,
		'paramtypes': [
			[Id, Number, MemRef, DoubleMemRef],
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
		'nargs': 0,
		'op': OP_VMRESUME,
		'paramtypes': []
	},
}

def doesInstructionExist(instruction):
	return instruction in _INSTR

def getInstructionLength(instruction):
	return 1 + _INSTR[instruction]['nargs']

def assembleInstruction(name, args, addr, symtab, defines):
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
	"""
	if not doesInstructionExist(name):
		raise InstructionError("Unknown instruction %s" % name)

	instr = _INSTR[name]

	if len(args) != instr['nargs']:
		raise InstructionError("Instruction %s expected %d arguments, got %d" % (name, instr['nargs'], len(args)))

	for i, arg in enumerate(args):
		if not type(arg) in instr['paramtypes'][i]:
			raise InstructionError("Unexpected argument for instruction %s at position %d of type %s" % (name, i+1, arg.__class__.__name__))
 
	privilegeLevel = 0
	
	operandValues = []
	operandTypes = []
	relocations = []
	importedSymbols = []

	#parse all arguments the instruction needs and gather the operand type, value, import and relocation information
	for n in range(instr['nargs']):
		(operandType, operandValue, importedSymbol, relocation) = _parseAgumentType(args[n], symtab)
		operandValues.append(operandValue)
		operandTypes.append(operandType)
		relocations.append(relocation)
		importedSymbols.append(importedSymbol)

	#create the instruction and operand sequence based on the number of arguments
	if instr['nargs'] == 0:
		assembled = [
			struct.pack("<BBBB", instr["op"], privilegeLevel, 0, 0)
		]
	elif instr['nargs'] == 1:
		assembled = [
			struct.pack("<BBBB", instr["op"], privilegeLevel, operandTypes[0], 0),
			struct.pack("<I", operandValues[0])
		]
	elif instr['nargs'] == 2:
		assembled = [
			struct.pack("<BBBB", instr["op"], privilegeLevel, operandTypes[0], operandTypes[1]),
			struct.pack("<I", operandValues[0]),
			struct.pack("<I", operandValues[1])
		]
	else:
		raise InstructionError("Instruction seems to need more than 2 arguments. This is an internal error in the assembler")

	#put everything into a container object and return it for further processing
	return AssembledInstruction(op=assembled, import_req=importedSymbols, reloc_req=relocations)

def _parseAgumentType(arg, symtab):
	#The argument is a symbolic name
	if isinstance(arg, Id):
		#check if labelname of the MemRef is locally defined
		#if it is, then we don't have an external symbol, but a relocation
		#otherwise we have a relocation
		if arg.id in symtab:
			return (PARAM_IMMEDIATE, symtab[arg.id].offset, None, symtab[arg.id].segment)
		else:
			return (PARAM_IMMEDIATE, 0, arg.id, None)

	#The argument is a number
	elif isinstance(arg, Number):
		return (PARAM_IMMEDIATE, arg.val, None, None)

	#The argument is a memory reference
	elif isinstance(arg, MemRef):
		#check if labelname of the MemRef is locally defined
		#if it is, then we don't have an external symbol, but a relocation
		#otherwise we have a relocation
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
			return (PARAM_MEMORY_SINGLE_DS, offset, externdefinedSymbol, relocation)
		elif arg.segment == 'es':
			return (PARAM_MEMORY_SINGLE_ES, offset, externdefinedSymbol, relocation)
		else:
			raise Exception("Unknown memory segment: %s" % arg.segment)

	#The argument is a double memory reference
	elif isinstance(arg, DoubleMemRef):
		#check if labelname of the MemRef is locally defined
		#if it is, then we don't have an external symbol, but a relocation
		#otherwise we have a relocation
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
			return (PARAM_MEMORY_DOUBLE_DS, offset, externdefinedSymbol, relocation)
		elif arg.segment == 'es':
			return (PARAM_MEMORY_DOUBLE_ES, offset, externdefinedSymbol, relocation)
		else:
			raise Exception("Unknown memory segment: %s" % arg.segment)

	else:
		raise InstructionError("Instruction got unknown argument type. Got '%s'" % arg.__class__.__name__)
