from common.Opcodes import *
from Exceptions import CPUStateError

class CPUState(object):
	def __init__(self):
		self.reset()

	def reset(self):
		#Segments
		self.CS = 0
		self.DS = 0
		self.ES = 0
		self.SS = 0
		self.RS = 0

		#Stack- and Instruction-Pointer
		self.IP = 0
		self.SP = 0

		#Flags
		self.Flags = 0

		#Misc
		#self.VmTbl = 0
		#self.VmID = 0
		self.privLvl = 0

	def getResultingInstructionAddress(self):
		return self.CS + self.IP

	def getResultingDataAddress(self, offset):
		return self.DS + offset

	def getResultingExtraAddress(self, offset):
		return self.ES + offset

	def getResultingStackAddress(self):
		return self.SS + self.SP

	def getRegisterAddress(self, reg):
		#check if reg < 31
		return self.RS + reg

	def setZeroFlag(self):
		self.Flags |= (1<<0)

	def clearZeroFlag(self):
		self.Flags &= ~(1<<0)

	def getZeroFlag(self):
		return (self.Flags & (1<<0)) != 0

	def setGreaterEqualFlag(self):
		self.Flags |= (1<<1)

	def clearGreaterEqual(self):
		self.Flags &= ~(1<<1)

	def getGreaterEqualFlag(self):
		return (self.Flags & (1<<1)) != 0

	def decrementStackPointer(self):
		self.SP -= 1
		self.SP &= 0xFFFFFFFF

	def incrementStackPointer(self):
		self.SP += 1
		self.SP &= 0xFFFFFFFF

	def getSpecialRegister(self, index):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		if index == SPECIALREG_SEGTBL:
			pass
		elif index == SPECIALREG_VMTBL:
			pass
		elif index == SPECIALREG_STACKPTR:
			return self.SP
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")
		

	def setSpecialRegister(self, index, value):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		if index == SPECIALREG_SEGTBL:
			pass
		elif index == SPECIALREG_VMTBL:
			pass
		elif index == SPECIALREG_STACKPTR:
			self.SP = value
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")

	#TODO: get string reprensation for printing the regs