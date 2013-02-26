from .CPUState import CPUState
from .Memory import Memory
from .Exceptions import SimulatorError, CPUSegmentViolationException

from common import Opcodes

import struct
import logging
import sys

from .Instructions import doesInstructionExist, getArgumentCount, areParametersValid

class CPU(object):
	def __init__(self, memoryString):
		self.state = CPUState()
		self.memory = Memory.createFromBinaryString(memoryString)
		self.logger = logging.getLogger('CPU')
		self.reset()

	def reset(self):
		self.state.reset(self.memory)

	def doSimulationStep(self):
		#todo check if pc can be fetched from the resulting address

		self.logger.debug("Fetching instruction from %x", self.state.IP)

		try:
			curWord = self.memory.readBinary(self.state.getResultingInstructionAddress())
			(opcode, privlvl, operandType1, operandType2) = struct.unpack("<BBBB", curWord)
		except CPUSegmentViolationException, e:
			self.raiseInterrupt(Opcodes.INTR_SEG_VIOL * 2, self.state.IP, [e.segment, e.offset])
			return True

		registerOperand1 = operandType1 & 0x1F
		operandType1 = operandType1 >> 5

		registerOperand2 = operandType2 & 0x1F
		operandType2 = operandType2 >> 5

		#check wether instruction itself exists and raise exception if not
		if not doesInstructionExist(opcode):
			self.logger.debug("Unknown instruction at physical 0x%x", self.state.getResultingInstructionAddress())
			self.raiseInterrupt(Opcodes.INTR_INVALID_INSTR * 2, self.state.IP)
			return True

		#check wether the operand types encoded in the instruction word are valid for the given opcode and raise exception if not
		if not areParametersValid(opcode, operandType1, operandType2):
			self.logger.debug("Invalid parameter type for instruction 0x%x at physical 0x%x", opcode, self.state.getResultingInstructionAddress())
			self.raiseInterrupt(Opcodes.INTR_INVALID_INSTR * 2, self.state.IP)
			return True

		if privlvl < self.state.privLvl:
			#TODO raise cpu exception
			print "!!!PrivLvl violation!!!"
			return False

		argumentCount = getArgumentCount(opcode)

		ipadd = 1
		operand1 = 0
		operand2 = 0

		writebackValue = None
		writebackFunction = None

		#decode first operand type, fetch it and prepare a writeback closure
		if argumentCount > 0:
			if operandType1 == Opcodes.PARAM_IMMEDIATE:
				operand1 = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				ipadd += 1

			elif operandType1 == Opcodes.PARAM_REGISTER:
				operand1 = self.state.getRegister(registerOperand1)
				writebackFunction = lambda val: self.state.setRegister(registerOperand1, val)

			elif operandType1 == Opcodes.PARAM_MEMORY_SINGLE_DS:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				if registerOperand1 != 31: operand1addr += self.state.getRegister(registerOperand1);
				operand1addr = self.state.getResultingDataAddress(operand1addr)
				operand1 = self.memory.readWord(operand1addr)
				writebackFunction = lambda val: self.memory.writeWord(operand1addr, val)
				ipadd += 1

			elif operandType1 == Opcodes.PARAM_MEMORY_SINGLE_ES:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				if registerOperand1 != 31: operand1addr += self.state.getRegister(registerOperand1)
				operand1addr = self.state.getResultingExtraAddress(operand1addr)
				operand1 = self.memory.readWord(operand1addr)
				writebackFunction = lambda val: self.memory.writeWord(operand1addr, val)
				ipadd += 1

			elif operandType1 == Opcodes.PARAM_MEMORY_DOUBLE_DS:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand1addr = self.memory.readWord(self.state.getResultingDataAddress(operand1addr))
				if registerOperand1 != 31: operand1addr += self.state.getRegister(registerOperand1)
				operand1addr = self.state.getResultingDataAddress(operand1addr);
				operand1 = self.memory.readWord(operand1addr)
				writebackFunction = lambda val: self.memory.writeWord(operand1addr, val)
				ipadd += 1

			elif operandType1 == Opcodes.PARAM_MEMORY_DOUBLE_ES:
				operand1addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand1addr = self.memory.readWord(self.state.getResultingExtraAddress(operand1addr))
				if registerOperand1 != 31: operand1addr += self.state.getRegister(registerOperand1)
				operand1addr = self.state.getResultingExtraAddress(operand1addr)
				operand1 = self.memory.readWord(operand1addr)
				writebackFunction = lambda val: self.memory.writeWord(operand1addr, val)
				ipadd += 1

			elif operandType1 == Opcodes.PARAM_SPECIAL_REGISTER:
				operand1 = self.state.getSpecialRegister(registerOperand1)
				writebackFunction = lambda val: self.state.setSpecialRegister(registerOperand1, val)

			else:
				self.logger.error("Unknown operand type for operand 1: %x", operandType1)
				return False
		
		#decode second operand type, fetch it and prepare a writeback closure
		if argumentCount > 1:
			if operandType2 == Opcodes.PARAM_IMMEDIATE:
				operand2 = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				ipadd += 1

			elif operandType2 == Opcodes.PARAM_REGISTER:
				operand2 = self.state.setRegister(registerOperand2)

			elif operandType2 == Opcodes.PARAM_MEMORY_SINGLE_DS:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				if registerOperand2 != 31: operand2addr += self.state.getRegister(registerOperand2)
				operand2 = self.memory.readWord(self.state.getResultingDataAddress(operand2addr))
				ipadd += 1

			elif operandType2 == Opcodes.PARAM_MEMORY_SINGLE_ES:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				if registerOperand2 != 31: operand2addr += self.state.getRegister(registerOperand2)
				operand2 = self.memory.readWord(self.state.getResultingExtraAddress(operand2addr))
				ipadd += 1

			elif operandType2 == Opcodes.PARAM_MEMORY_DOUBLE_DS:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand2addr = self.memory.readWord(self.state.getResultingDataAddress(operand2addr))
				if registerOperand2 != 31: operand2addr += self.state.getRegister(registerOperand2)
				operand2addr = self.state.getResultingDataAddress(operand2addr);
				operand2 = self.memory.readWord(operand2addr)
				ipadd += 1

			elif operandType2 == Opcodes.PARAM_MEMORY_DOUBLE_ES:
				operand2addr = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
				operand2addr = self.memory.readWord(self.state.getResultingExtraAddress(operand2addr))
				if registerOperand2 != 31: operand2addr += self.state.getRegister(registerOperand2)
				operand2addr = self.state.getResultingExtraAddress(operand2addr);
				operand2 = self.memory.readWord(operand2addr)
				ipadd += 1

			elif operandType2 == Opcodes.PARAM_SPECIAL_REGISTER:
				operand2 = self.state.getSpecialRegister(registerOperand2)

			else:
				self.logger.error("Unknown operand type for operand 2: %x", operandType2)
				return False


		#TODO: if memory is involved, check segment violations

		#handle opcode

		#ADD
		if opcode == Opcodes.OP_ADD:
			#print "OP_ADD"
			writebackValue = (operand1 + operand2) & 0xFFFFFFFF

		#SUB
		elif opcode == Opcodes.OP_SUB:
			#print "OP_SUB"
			#TODO 2er komplement foo?
			writebackValue = (operand1 - operand2) & 0xFFFFFFFF

		#MUL
		elif opcode == Opcodes.OP_MUL:
			#print "Opcodes.OP_MUL"
			writebackValue = (operand1 * operand2) & 0xFFFFFFFF

		#DIV
		elif opcode == Opcodes.OP_DIV:
			#print "Opcodes.OP_DIV"
			if operand2 == 0:
				self.logger.debug("Division by zero occured at physical 0x%x", self.state.getResultingInstructionAddress())
				self.raiseInterrupt(Opcodes.INTR_DIV_BY_ZERO * 2, self.state.IP)
				return True

			writebackValue = (operand1 / operand2) & 0xFFFFFFFF

		#MOD
		elif opcode == Opcodes.OP_MOD:
			#print "OP_MOD"
			writebackValue = (operand1 % operand2) & 0xFFFFFFFF

		#OR
		elif opcode == Opcodes.OP_OR:
			#print "OP_OR"
			writebackValue = operand1 | operand2

		#XOR
		elif opcode == Opcodes.OP_XOR:
			#print "OP_XOR"
			writebackValue = operand1 ^ operand2

		#AND
		elif opcode == Opcodes.OP_AND:
			#print "OP_AND"
			writebackValue = operand1 & operand2

		#NOT
		elif opcode == Opcodes.OP_NOT:
			#print "OP_NOT"
			writebackValue = operand1 ^ operand2

		#MOV
		elif opcode == Opcodes.OP_MOV:
			#print "OP_MOV"
			writebackValue = operand2

		#NOP
		elif opcode == Opcodes.OP_NOP:
			pass

		#HALT
		elif opcode == Opcodes.OP_HALT:
			#print "Opcodes.OP_HALT"
			return False

		#PRINT
		elif opcode == Opcodes.OP_PRINT:
			#print "Opcodes.OP_PRINT"
			sys.stdout.write(chr(operand1 & 0xFF))
			sys.stdout.flush()

		#CMP
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

		#JMP
		elif opcode == Opcodes.OP_JMP:
			#print "Opcodes.OP_JMP to 0x%x" % operand1
			self.state.IP = operand1
			return True

		#JZ
		elif opcode == Opcodes.OP_JZ:
			#print "Opcodes.OP_JZ"
			if self.state.getZeroFlag():
				self.state.IP = operand1
				return True

		#JNZ
		elif opcode == Opcodes.OP_JNZ:
			#print "Opcodes.OP_JNZ"
			if not self.state.getZeroFlag():
				self.state.IP = operand1
				return True

		#JGT
		elif opcode == Opcodes.OP_JGT:
			#print "Opcodes.OP_JGT"
			if self.state.getGreaterEqualFlag() and (not self.state.getZeroFlag()):
				self.state.IP = operand1
				return True

		#JGE
		elif opcode == Opcodes.OP_JGE:
			#print "Opcodes.OP_JGE"
			if self.state.getGreaterEqualFlag():
				self.state.IP = operand1
				return True

		#CALL
		elif opcode == Opcodes.OP_CALL:
			#push return address
			self.pushToStack(self.state.IP + ipadd)

			#set new IP
			self.state.IP = operand1
			return True

		#RET
		elif opcode == Opcodes.OP_RET:
			#get new IP from stack
			self.state.IP = self.popFromStack()
			return True
		
		#PUSH
		elif opcode == Opcodes.OP_PUSH:
			self.pushToStack(operand1)

		#POP
		elif opcode == Opcodes.OP_POP:
			writebackValue = self.popFromStack()

		#INT
		elif opcode == Opcodes.OP_INT:
			self.raiseInterrupt((operand1 + Opcodes.INTR_SOFTWARE) * 2, self.state.IP + ipadd)
			return True

		#RETI
		elif opcode == Opcodes.OP_RETI:
			self.state.IP = self.popFromStack()
			return True

		#VMRESUME
		elif opcode == Opcodes.OP_VMRESUME:
			print "Opcodes.OP_VMRESUME"

		#Unknown - internal error
		else:
			self.logger.error("Internal simulator error: Don't know how to simulate instruction %x. I'm so sorry! :(", opcode)
			return False


		#perform writeback if necessary
		if writebackValue != None:
			if argumentCount == 0:
				self.logger.error("Internal simulator error: Can't do writeback on 0-operand instructions")
				return False

			if writebackFunction == None:
				self.logger.error("Internal simulator error: Instruction wants to perform writeback, but callback is None")
				return False

			writebackFunction(writebackValue)

		#advance instruction pointer
		self.state.IP += ipadd

		return True

	def pushToStack(self, value):
		self.state.decrementStackPointer()
		self.memory.writeWord(self.state.getResultingStackAddress(), value)

	def popFromStack(self):
		stackValue = self.memory.readWord(self.state.getResultingStackAddress())
		self.state.incrementStackPointer()
		return stackValue

	def raiseSegmentViolation(self, segmentIndex):
		self.raiseInterrupt(INTR_SEG_VIOL * 2, self.state.IP, [segmentIndex])

	def raiseInterrupt(self, interruptNumber, returnIp, additionalStackValues = []):
		if interruptNumber > 32:
			raise SimulatorError("Interrupt number is out of bounds")

		if not self.state.InVM:
			map(lambda x: self.pushToStack(x), additionalStackValues)
			self.pushToStack(returnIp)
			self.state.IP = self.state.getResultingCodeAddress(interruptNumber)
		else:
			#TODO restore HV context via vmtbl and raise hypervisor trap
			raise Exception("interrupt in VM not implemented")
