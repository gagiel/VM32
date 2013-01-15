from common.Opcodes import *
from Exceptions import CPUStateError

from collections import namedtuple

SegmentEntry = namedtuple("SegmentEntry", ["start", "limit", "type"])

class CPUState(object):
	def __init__(self):
		self.reset(None)

	def reset(self, memory):
		self.memory = memory

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
		self.VmTbl = 0
		self.SegTbl = 0

		#self.VmID = 0
		self.privLvl = 0

		self.segments = []

	def getResultingInstructionAddress(self):
		#TODO: check if segment exists, check if limit is violated, check if type matches and check if privLvl is not violated

		if len(self.segments) == 0:
			return self.IP
		else:
			return segments[self.CS].start + self.IP

	def getResultingDataAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			return segments[self.DS].start + offset

	def getResultingExtraAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			return segments[self.ES].start + offset

	def getResultingStackAddress(self):
		if len(self.segments) == 0:
			return self.SP
		else:
			return segments[self.SS].start + self.SP

	def getRegister(self, reg):
		if reg < 0 or reg > 30:
			raise CPUStateError("Can't access register smaller than 0 or bigger than 30")

		if len(self.segments) == 0:
			return self.memory.readWord(0x2000 + reg)
		else:
			return self.memory.readWord(segments[self.RS].start + reg)

	def setRegister(self, reg, value):
		if reg < 0 or reg > 30:
			raise CPUStateError("Can't access register smaller than 0 or bigger than 30")

		if len(self.segments) == 0:
			self.memory.writeWord(0x2000 + reg, value)
		else:
			self.memory.writeWord(segments[self.RS].start + reg, value)

	def getFlags(self):
		return self.Flags

	def setFlags(self, flags):
		self.Flags = flags

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
		#TODO check segment limits

		self.SP -= 1
		self.SP &= 0xFFFFFFFF

	def incrementStackPointer(self):
		#TODO check segment limits
		
		self.SP += 1
		self.SP &= 0xFFFFFFFF

	def getSpecialRegister(self, index):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		if index == SPECIALREG_SEGTBL:
			return self.SegTbl
		elif index == SPECIALREG_VMTBL:
			return self.VmTbl
		elif index == SPECIALREG_STACKPTR:
			return self.SP
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")
		

	def setSpecialRegister(self, index, value):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		if index == SPECIALREG_SEGTBL:
			self.SegTbl = value
		elif index == SPECIALREG_VMTBL:
			self.VmTbl = value
		elif index == SPECIALREG_STACKPTR:
			self.SP = value
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")

	def _parseNewSetbl(self, address):
		self.segments = []

		while True:
			start = self.memory.readWord(address)
			address += 1
			limit = self.memory.readWord(address)
			address += 1
			type = self.memory.readWord(address)
			address += 1
			privLvl = self.memory.readWord(address)

			if start == 0 and limit == 0 and type == 0 and privLvl == 0:
				break

			if not type in SEGMENT_TYPES:
				raise CPUStateSegTblFaultyError("Unknown segment type encountered")

			if type == SEGMENT_RS and limit != 31:
				raise CPUStateSegTblFaultyError("Register segments need to have a limit of 31")

			self.segments.add(SegmentEntry(start, limit, type, privLvl))

	#TODO: get string reprensation for printing the regs