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
		#check timer for expiration
		if self.state.isInterruptPending() and self.state.isInterruptEnabled():
			self.state.resetInterruptPending()
			self.raiseTimerInterrupt()
		else:
			self.state.handleHardwareTimerTick()

		self.logger.debug("Fetching instruction from %x", self.state.IP)

		try:
			curWord = self.memory.readBinary(self.state.getResultingInstructionAddress())
			(opcode, privlvl, operandType1, operandType2) = struct.unpack("<BBBB", curWord)
		except CPUSegmentViolationException, e:
			self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
			return True

		registerOperand1 = operandType1 & 0x1F
		operandType1 = operandType1 >> 5

		registerOperand2 = operandType2 & 0x1F
		operandType2 = operandType2 >> 5

		#check wether instruction itself exists and raise exception if not
		if not doesInstructionExist(opcode):
			self.logger.debug("Unknown instruction at physical 0x%x", self.state.IP)
			self.raiseInterrupt(Opcodes.INTR_INVALID_INSTR, self.state.IP)
			return True

		#check wether the operand types encoded in the instruction word are valid for the given opcode and raise exception if not
		if not areParametersValid(opcode, operandType1, operandType2):
			self.logger.debug("Invalid parameter type for instruction 0x%x at physical 0x%x", opcode, self.state.IP)
			self.raiseInterrupt(Opcodes.INTR_INVALID_INSTR, self.state.IP)
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
			try:
				if operandType1 == Opcodes.PARAM_IMMEDIATE:
					operand1 = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
					ipadd += 1

				elif operandType1 == Opcodes.PARAM_REGISTER:
					if registerOperand1 > 30:
						self.logger.debug("Invalid register access for instruction 0x%x at physical 0x%x", opcode, self.state.IP)
						self.raiseInterrupt(Opcodes.INTR_INVALID_INSTR, self.state.IP)
						return True

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
					operand1 = self.getSpecialRegister(registerOperand1)
					writebackFunction = lambda val: self.setSpecialRegister(registerOperand1, val)

				else:
					self.logger.error("Unknown operand type for operand 1: %x", operandType1)
					return False

			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True
		
		#decode second operand type and fetch it
		if argumentCount > 1:
			try:
				if operandType2 == Opcodes.PARAM_IMMEDIATE:
					operand2 = self.memory.readWord(self.state.getResultingInstructionAddress() + ipadd)
					ipadd += 1

				elif operandType2 == Opcodes.PARAM_REGISTER:
					if registerOperand1 > 30:
						self.logger.debug("Invalid register access for instruction 0x%x at physical 0x%x", opcode, self.state.IP)
						self.raiseInterrupt(Opcodes.INTR_INVALID_INSTR, self.state.IP)
						return True

					operand2 = self.state.getRegister(registerOperand2)

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
					operand2 = self.getSpecialRegister(registerOperand2)

				else:
					self.logger.error("Unknown operand type for operand 2: %x", operandType2)
					return False
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True

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
				self.logger.debug("Division by zero occured at physical 0x%x", self.state.IP)
				self.raiseInterrupt(Opcodes.INTR_DIV_BY_ZERO, self.state.IP)
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

		#SHL
		elif opcode == Opcodes.OP_SHL:
			#print "OP_SHL"
			writebackValue = (operand1 << operand2) & 0xFFFFFFFF

		#SHR
		elif opcode == Opcodes.OP_SHR:
			#print "OP_SHR"
			writebackValue = (operand1 >> operand2) & 0xFFFFFFFF

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
			if not self.state.InVM:
				return False
			else:
				self.state.IP += ipadd
				self.raiseVMExitEvent(Opcodes.HVTRAP_HALT, [operand1 & 0xFF])
				return True

		#PRINT
		elif opcode == Opcodes.OP_PRINT:
			#print "Opcodes.OP_PRINT"
			if not self.state.InVM:
				sys.stdout.write(chr(operand1 & 0xFF))
				sys.stdout.flush()
			else:
				self.state.IP += ipadd
				self.raiseVMExitEvent(Opcodes.HVTRAP_HARDWARE_ACCESS, [operand1 & 0xFF])
				return True

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
			try:
				self.pushToStack(self.state.IP + ipadd)

				#set new IP
				self.state.IP = operand1
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])

			return True

		#RET
		elif opcode == Opcodes.OP_RET:
			#get new IP from stack
			try:
				self.state.IP = self.popFromStack()
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])

			return True

		#RETN
		elif opcode == Opcodes.OP_RETN:
			#get new IP from stack
			try:
				self.state.IP = self.popFromStack()
				for i in range(operand1): self.state.incrementStackPointer()
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])

			return True
		
		#PUSH
		elif opcode == Opcodes.OP_PUSH:
			try:
				self.pushToStack(operand1)
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True

		#POP
		elif opcode == Opcodes.OP_POP:
			try:
				writebackValue = self.popFromStack()
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True

		#ENTER
		elif opcode == Opcodes.OP_ENTER:
			try:
				self.pushToStack(self.state.getRegister(29))			#push basepointer
				self.state.setRegister(29, self.state.getRegister(30))	#set new basepointer
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True

		#LEAVE
		elif opcode == Opcodes.OP_LEAVE:
			try:
				self.state.setRegister(29, self.popFromStack())
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True

		#GETARGUMENT
		elif opcode == Opcodes.OP_GETARGUMENT:
			try:
				writebackValue = self.memory.readWord(self.state.getRegister(29) + 2 + operand2)
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])
				return True

		#INT
		elif opcode == Opcodes.OP_INT:
			try:
				self.raiseInterrupt((operand1 + Opcodes.INTR_SOFTWARE), self.state.IP + ipadd)
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])

			return True

		#RETI
		elif opcode == Opcodes.OP_RETI:
			try:
				self.state.IP = self.popFromStack()
			except CPUSegmentViolationException, e:
				self.raiseInterrupt(Opcodes.INTR_SEG_VIOL, self.state.IP, [e.segment, e.offset])

			return True

		#VMRESUME
		elif opcode == Opcodes.OP_VMRESUME:
			if not self.state.InVM:
				self.state.IP += ipadd
				self.state.saveHypervisorContext()
				self.state.setVmContext(operand1)
			else:
				print "vmresume in vm"
				#self.raiseHypervisorTrap(Opcodes.HVTRAP_VMRESUME, [operand1])

			return True

		#CLI
		elif opcode == Opcodes.OP_CLI:
			self.state.disableInterrupts()

		#STI
		elif opcode == Opcodes.OP_STI:
			self.state.enableInterrupts()

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

	def raiseInterrupt(self, interruptNumber, returnIp, additionalStackValues = []):
		if interruptNumber > 32:
			raise SimulatorError("Interrupt number is out of bounds")

		if not self.state.InVM:
			try:
				map(lambda x: self.pushToStack(x), additionalStackValues)
				self.pushToStack(returnIp)
				self.state.IP = self.state.getResultingInterruptAddress() + interruptNumber * 2
			except CPUSegmentViolationException, e:
				print "ERROR! CPU can't push values to the stack for interrupt/exception handling, the CPU is now in an undefined state and likely to crash"
				raise e
		else:
			softwareInterruptNumber = 0
			if interruptNumber >= Opcodes.INTR_SOFTWARE:
				softwareInterruptNumber = interruptNumber - Opcodes.INTR_SOFTWARE
				additionalStackValues = [softwareInterruptNumber]
				interruptNumber = INTR_SOFTWARE

			hvTrapNumber = Opcodes.INTR_TO_HVTRAP[interruptNumber]
			self.raiseVMExitEvent(hvTrapNumber, additionalStackValues)

	def raiseTimerInterrupt(self):
		if not self.state.InVM:
			self.pushToStack(self.state.IP)
			self.state.IP = self.state.getResultingInterruptAddress() + Opcodes.INTR_TIMER * 2
		else:
			currentvm = self.state.VmID
			self.state.saveVmContext(currentvm)	#save current vm state
			self.state.setVmContext(0)	#switch to hypervisor state
			self.state.InVM = False		#we are no longer inside of a VM

			#prepare information for vmexit handler
			self.pushToStack(Opcodes.HVTRAP_TIMER)
			self.pushToStack(currentvm)

			#jump to timer interrupt handler in hv context with return address pointing to next instruction after VMRESUME
			self.pushToStack(self.state.IP)
			self.state.IP = self.state.getResultingInterruptAddress() + Opcodes.INTR_TIMER * 2

	def raiseVMExitEvent(self, trapNumber, additionalStackValues=[]):
		currentvm = self.state.VmID
		self.state.saveVmContext(currentvm)	#save current vm state
		self.state.setVmContext(0)	#switch to hypervisor state
		self.state.InVM = False		#we are no longer inside of a VM

		try:
			map(lambda x: self.pushToStack(x), additionalStackValues)
			self.pushToStack(trapNumber)
			self.pushToStack(currentvm)
		except CPUSegmentViolationException, e:
			print "ERROR! CPU can't push values to the stack for VMEXIT event, the CPU is now in an undefined state and likely to crash"
			raise e

	def setSpecialRegister(self, specialRegister, value):
		if not self.state.InVM:
			self.state.setSpecialRegister(specialRegister, value)
		else:
			self.raiseVMExitEvent(Opcodes.HVTRAP_SPECIAL_REG_WRITE, [value, specialRegister])

	def getSpecialRegister(self, specialRegister):
		if not self.state.InVM:
			return self.state.getSpecialRegister(specialRegister)
		else:
			self.raiseVMExitEvent(Opcodes.HVTRAP_SPECIAL_REG_READ, [specialRegister])
