import struct

from common.Opcodes import *
from Parser import Number, Id, String, MemRef, DoubleMemRef, Instruction, Directive, LabelDef
from Exceptions import InstructionError

class AssembledInstruction(object):
	def __init__(self, op=None, import_req=None, reloc_req=None):
		self.op = op
		self.import_req = import_req
		self.reloc_req = reloc_req

def _assemble_arithmetic_cmp(instruction, args, addr, symtab, defines):
	pass

def _assemble_mov(instruction, args, addr, symtab, defines):
	pass

def _assemble_noargs(instruction, args, addr, symtab, defines):
	pass

def _assemble_print(instruction, args, addr, symtab, defines):
	pass

def _assemble_cmp(instruction, args, addr, symtab, defines):
	pass

def _assemble_branch(instruction, args, addr, symtab, defines):
	#possible args:
	#Id
	#Number
	#MemRef
	#DoubleMemRef

	arg = args[0]
	destination = 0
	operandType = PARAM_IMMEDIATE
	privilegeLevel = 0

	if isinstance(arg, Id):
		if not arg.id in symtab:
			raise InstructionError("Undefined label: %s" % arg.id)

		dest = symtab[arg.id]
		if dest.segment != addr.segment:
			raise InstructionError("Branch target is in different segment")

		destination = symtab[arg.id].offset
		operandType = PARAM_IMMEDIATE
	elif isinstance(arg, Number):
		destination = arg.val
		operandType = PARAM_IMMEDIATE
	elif isinstance(arg, MemRef):
		raise Exception("Not implemented")
	elif isinstance(arg, DoubleMemRef):
		raise Exception("Not implemented")
	else:
		raise InstructionError("Branch instruction got wrong argument type")

	assembled = [struct.pack("<BBBB", instruction['op'], privilegeLevel, operandType, 0), struct.pack("<I", destination)]
	return AssembledInstruction(op= assembled)

def _assemble_stack(instruction, args, addr, symtab, defines):
	pass

def _assemble_int(instruction, args, addr, symtab, defines):
	pass

_INSTR = {
	'add': {
		'nargs': 2,
		'op': OP_ADD,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'sub': {
		'nargs': 2,
		'op': OP_SUB,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'mul': {
		'nargs': 2,
		'op': OP_MUL,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'div': {
		'nargs': 2,
		'op': OP_DIV,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'mod': {
		'nargs': 2,
		'op': OP_MOD,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},

	'or': {
		'nargs': 2,
		'op': OP_OR,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'xor': {
		'nargs': 2,
		'op': OP_XOR,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'and': {
		'nargs': 2,
		'op': OP_AND,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},
	'not': {
		'nargs': 2,
		'op': OP_NOT,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},

	'mov': {
		'nargs': 2,
		'op': OP_MOV,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES, PARAM_SPECIAL_REGISTER],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES, PARAM_SPECIAL_REGISTER],
		'func': _assemble_mov
	},

	'nop': {
		'nargs': 0,
		'op': OP_NOP,
		'param1types': [],
		'param2types': [],
		'func': _assemble_noargs
	},
	'halt': {
		'nargs': 0,
		'op': OP_HALT,
		'param1types': [],
		'param2types': [],
		'func': _assemble_noargs
	},


	'print': {
		'nargs': 1,
		'op': OP_PRINT,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_print
	},


	'cmp': {
		'nargs': 2,
		'op': OP_CMP,
		'param1types': [PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'func': _assemble_arithmetic_cmp
	},


	'jmp': {
		'nargs': 1,
		'op': OP_JMP,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_branch
	},
	'jz': {
		'nargs': 1,
		'op': OP_JZ,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_branch
	},
	'jnz': {
		'nargs': 1,
		'op': OP_JNZ,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_branch
	},
	'jgt': {
		'nargs': 1,
		'op': OP_JGT,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_branch
	},
	'call': {
		'nargs': 1,
		'op': OP_CALL,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_branch
	},
	'ret': {
		'nargs': 0,
		'op': OP_RET,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_branch
	},

	'push': {
		'nargs': 1,
		'op': OP_PUSH,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_stack
	},
	'pop': {
		'nargs': 1,
		'op': OP_POP,
		'param1types': [PARAM_IMMEDIATE, PARAM_MEMORY_SINGLE_DS, PARAM_MEMORY_SINGLE_ES, PARAM_MEMORY_DOUBLE_DS, PARAM_MEMORY_DOUBLE_ES],
		'param2types': [],
		'func': _assemble_stack
	},


	'int': {
		'nargs': 1,
		'op': OP_INT,
		'param1types': [PARAM_IMMEDIATE],
		'param2types': [],
		'func': _assemble_int
	},


	'reti': {
		'nargs': 0,
		'op': OP_RETI,
		'param1types': [],
		'param2types': [],
		'func': _assemble_noargs
	},
	'vmresume': {
		'nargs': 0,
		'op': OP_VMRESUME,
		'param1types': [],
		'param2types': [],
		'func': _assemble_noargs
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

	instructions = instr['func'](instr, args, addr, symtab, defines)

	if isinstance(instructions, list):
		return instructions
	else:
		return [instructions]
