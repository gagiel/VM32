from .CPUState import CPUState
from .Memory import Memory

from common import Opcodes

import struct
import logging

from .Instructions import doesInstructionExist, getArgumentCount

#Interrupt types
INTR_RESET = 0
INTR_SEG_VIOL = 1
INTR_INVALID_INSTR = 2
INTR_DIV_BY_ZERO = 3
INTR_HV_TRAP = 4
INTR_TIMTER = 5
INTR_SOFTWARE = 6

class CPU(object):
	def __init__(self, memoryString):
		self.state = CPUState()
		self.memory = Memory.createFromBinaryString(memoryString)
		self.logger = logging.getLogger('CPU')
		self.reset()

	def reset(self):
		self.state.reset()

	def doSimulationStep(self):
		#todo check if pc can be fetched from the resulting address

		self.logger.debug("Fetching instruction from %x", self.state.getResultingInstructionAddress()*4)

		curWord = self.memory.readBinary(self.state.getResultingInstructionAddress())
		(opcode, privlvl, operandType1, operandType2) = struct.unpack("<BBBB", curWord)

		operandType1 = operandType1 >> 5
		operandType2 = operandType2 >> 5

		if not doesInstructionExist(opcode):
			#TODO raise cpu exception, remove error-log
			self.logger.error("Unknown instruction")
			return

		if privlvl < self.state.privLvl:
			#TODO raise cpu exception
			print "!!!PrivLvl violation!!!"
			return

		argumentCount = getArgumentCount(opcode)

		ipadd = 1
		operand1 = 0
		operand2 = 0

		if argumentCount > 0:
			if operandType1 == Opcodes.PARAM_IMMEDIATE:
				operand1 = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				ipadd += 1
			elif operandType1 == Opcodes.PARAM_REGISTER:
				pass
			elif operandType1 == Opcodes.PARAM_MEMORY_SINGLE_DS:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand1 = self.memory.readWord(self.state.getResultingDataAddress(operand1addr))
				ipadd += 1
			elif operandType1 == Opcodes.PARAM_MEMORY_SINGLE_ES:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand1 = self.memory.readWord(self.state.getResultingExtraAddress(operand1addr))
				ipadd += 1
			elif operandType1 == Opcodes.PARAM_MEMORY_DOUBLE_DS:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand1addr = self.memory.readWord(self.state.getResultingDataAddress(operand1addr))
				operand1 = self.memory.readWord(self.state.getResultingDataAddress(operand1addr))
				ipadd += 1
			elif operandType1 == Opcodes.PARAM_MEMORY_DOUBLE_ES:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand1addr = self.memory.readWord(self.state.getResultingDataAddress(operand1addr))
				operand1 = self.memory.readWord(self.state.getResultingExtraAddress(operand1addr))
				ipadd += 1
			elif operandType1 == Opcodes.PARAM_SPECIAL_REGISTER:
				pass
			else:
				self.logger.error("Unknown operand type for operand 1: %x", operandType1)
				return
		
		if argumentCount > 1:
			if operandType2 == Opcodes.PARAM_IMMEDIATE:
				operand2 = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				ipadd += 1
			elif operandType2 == Opcodes.PARAM_REGISTER:
				pass
			elif operandType2 == Opcodes.PARAM_MEMORY_SINGLE_DS:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand2 = self.memory.readWord(self.state.getResultingDataAddress(operand2addr))
				ipadd += 1
			elif operandType2 == Opcodes.PARAM_MEMORY_SINGLE_ES:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand2 = self.memory.readWord(self.state.getResultingExtraAddress(operand2addr))
				ipadd += 1
			elif operandType2 == Opcodes.PARAM_MEMORY_DOUBLE_DS:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand2addr = self.memory.readWord(self.state.getResultingDataAddress(operand2addr))
				operand2 = self.memory.readWord(self.state.getResultingDataAddress(operand2addr))
				ipadd += 1
			elif operandType2 == Opcodes.PARAM_MEMORY_DOUBLE_ES:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand2addr = self.memory.readWord(self.state.getResultingDataAddress(operand2addr))
				operand2 = self.memory.readWord(self.state.getResultingExtraAddress(operand2addr))
				ipadd += 1
			elif operandType2 == Opcodes.PARAM_SPECIAL_REGISTER:
				pass
			else:
				self.logger.error("Unknown operand type for operand 2: %x", operandType2)
				return


		#TODO: parse args
		#TODO: check args for validity
		#TODO: if memory is involved, check segment violations

		if opcode == Opcodes.OP_ADD:
			print "OP_ADD"
		
		elif opcode == Opcodes.OP_SUB:
			print "OP_SUB"
		
		elif opcode == Opcodes.OP_MUL:
			print "Opcodes.OP_MUL"
		
		elif opcode == Opcodes.OP_DIV:
			print "Opcodes.OP_DIV"
		
		elif opcode == Opcodes.OP_MOD:
			print "OP_MOD"
		
		elif opcode == Opcodes.OP_OR:
			print "OP_OR"
		
		elif opcode == Opcodes.OP_XOR:
			print "OP_XOR"
		
		elif opcode == Opcodes.OP_AND:
			print "OP_AND"
		
		elif opcode == Opcodes.OP_NOT:
			print "OP_NOT"
		
		elif opcode == Opcodes.OP_MOV:
			print "OP_MOV"
		
		elif opcode == Opcodes.OP_NOP:
			pass
		
		elif opcode == Opcodes.OP_HALT:
			print "Opcodes.OP_HALT"
		
		elif opcode == Opcodes.OP_PRINT:
			#print "Opcodes.OP_PRINT"
			print chr(operand1)

		elif opcode == Opcodes.OP_CMP:
			#print "Opcodes.OP_CMP"
			if operand1 >= operand2:
				self.state.setGreaterEqualFlag()
			else:
				self.state.clearGreaterEqualFlag()

			if operand1 == operand2:
				self.state.setZeroFlag()
			else:
				self.state.clearZeroFlag()

		elif opcode == Opcodes.OP_JMP:
			#print "Opcodes.OP_JMP"
			self.state.IP = operand1
			return
		
		elif opcode == Opcodes.OP_JZ:
			#print "Opcodes.OP_JZ"
			if self.state.getZeroFlag():
				self.state.IP = operand1
				return

		elif opcode == Opcodes.OP_JNZ:
			#print "Opcodes.OP_JNZ"
			if not self.state.getZeroFlag():
				self.state.IP = operand1
				return

		elif opcode == Opcodes.OP_JGT:
			#print "Opcodes.OP_JGT"
			if self.state.getGreaterEqualFlag() and (not self.state.getZeroFlag()):
				self.state.IP = operand1
				return

		elif opcode == Opcodes.OP_JGE:
			#print "Opcodes.OP_JGE"
			if self.state.getGreaterEqualFlag():
				self.state.IP = operand1
				return
		
		elif opcode == Opcodes.OP_CALL:
			print "Opcodes.OP_CALL"
		
		elif opcode == Opcodes.OP_RET:
			print "Opcodes.OP_RET"
		
		elif opcode == Opcodes.OP_PUSH:
			print "Opcodes.OP_PUSH"
		
		elif opcode == Opcodes.OP_POP:
			print "Opcodes.OP_POP"
		
		elif opcode == Opcodes.OP_INT:
			print "Opcodes.OP_INT"
		
		elif opcode == Opcodes.OP_RETI:
			print "Opcodes.OP_RETI"
		
		elif opcode == Opcodes.OP_VMRESUME:
			print "Opcodes.OP_VMRESUME"
		
		else:
			self.logger.error("Internal simulator error: Don't know how to simulate instruction %x. I'm so sorry! :(", opcode)



		#TODO writeback

		self.state.IP += ipadd


	def raiseInterrupt(self):
		return
