from common.Opcodes import *
from Exceptions import CPUStateError, CPUStateSegTblFaultyError, CPUSegmentViolationException

from collections import namedtuple

SegmentEntry = namedtuple("SegmentEntry", ["start", "limit", "type", "privLvl"])

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

		self.InVM = False
		#self.VmID = 0

		self.privLvl = 0

		self.segments = []

	def getResultingInstructionAddress(self):
		#TODO: check if segment exists, check if limit is violated, check if type matches and check if privLvl is not violated

		if len(self.segments) == 0:
			return self.IP
		else:
			if self.IP < self.segments[self.CS].start or self.IP > self.segments[self.CS].limit:
				raise CPUSegmentViolationException(SEGMENT_CODE, self.IP)

			return self.IP

			#if self.segments[self.CS].start + self.IP > self.segments[self.CS].limit or self.IP < 0:
			#	raise CPUSegmentViolationException(SEGMENT_CODE, self.IP)


			#return self.segments[self.CS].start + self.IP

	def getResultingCodeAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			if offset < self.segments[self.CS].start or offset > self.segments[self.CS].limit:
				raise CPUSegmentViolationException(SEGMENT_CODE, offset)

			return offset

			#if self.segments[self.CS].start + offset > self.segments[self.CS].limit or offset < 0:
			#	raise CPUSegmentViolationException(SEGMENT_CODE, offset)

			#return self.segments[self.CS].start + offset

	def getResultingDataAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			#if self.segments[self.DS].start + offset > self.segments[self.DS].limit or offset < 0:
			#	print "start: %x - offset: %x - limit: %x" % (self.segments[self.DS].start, offset, self.segments[self.DS].limit)
			#	raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			#return self.segments[self.DS].start + offset

			if offset < self.segments[self.DS].start or offset > self.segments[self.DS].limit:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			return offset

	def getResultingExtraAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			#if self.segments[self.ES].start + offset > self.segments[self.ES].limit or offset < 0:
			#	raise CPUSegmentViolationException(SEGMENT_EXTRA, offset)

			#return self.segments[self.ES].start + offset

			if offset < self.segments[self.ES].start or offset > self.segments[self.ES].limit:
				raise CPUSegmentViolationException(SEGMENT_EXTRA, offset)

			return offset

	def getResultingStackAddress(self):
		if len(self.segments) == 0:
			return self.SP
		else:
			#if self.segments[self.SS].start + self.SS > self.segments[self.SS].limit or self.SS < 0:
			#	raise CPUSegmentViolationException(SEGMENT_STACK, self.SS)

			#return self.segments[self.SS].start + self.SP

			if self.SP < self.segments[self.SS].start or self.SP > self.segments[self.SS].limit:
				raise CPUSegmentViolationException(SEGMENT_STACK, self.SP)

			return self.SP

	def getRegister(self, reg):
		if reg < 0 or reg > 30:
			raise CPUStateError("Can't access register smaller than 0 or bigger than 30")

		if len(self.segments) == 0:
			return self.memory.readWord(0x2000 + reg)
		else:
			return self.memory.readWord(self.segments[self.RS].start + reg)

	def setRegister(self, reg, value):
		if reg < 0 or reg > 30:
			raise CPUStateError("Can't access register smaller than 0 or bigger than 30")

		if len(self.segments) == 0:
			self.memory.writeWord(0x2000 + reg, value)
		else:
			self.memory.writeWord(self.segments[self.RS].start + reg, value)

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
		elif index == SPECIALREG_CS:
			return self.CS
		elif index == SPECIALREG_DS:
			return self.DS
		elif index == SPECIALREG_ES:
			return self.ES
		elif index == SPECIALREG_RS:
			return self.RS
		elif index == SPECIALREG_SS:
			return self.SS
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")
		

	def setSpecialRegister(self, index, value):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		if index == SPECIALREG_SEGTBL:
			self.SegTbl = value
			self._parseNewSegTbl()
		elif index == SPECIALREG_VMTBL:
			self.VmTbl = value
		elif index == SPECIALREG_STACKPTR:
			self.SP = value
		elif index == SPECIALREG_CS:
			self.CS = value
		elif index == SPECIALREG_DS:
			self.DS = value
		elif index == SPECIALREG_ES:
			self.ES = value
		elif index == SPECIALREG_RS:
			self.RS = value
		elif index == SPECIALREG_SS:
			self.SS = value
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")

	def _parseNewSegTbl(self):
		self.segments = []

		address = self.SegTbl
		while True:
			start = self.memory.readWord(address)
			address += 1
			limit = self.memory.readWord(address)
			address += 1
			type = self.memory.readWord(address)
			address += 1
			privLvl = self.memory.readWord(address)
			address += 1

			if start == 0 and limit == 0 and type == 0 and privLvl == 0:
				break

			if not type in SEGMENT_TYPES:
				raise CPUStateSegTblFaultyError("Unknown segment type encountered")

			if type == SEGMENT_REGISTER and (limit - start) != 31:
				raise CPUStateSegTblFaultyError("Register segments need to have a size of 31")

			self.segments.append(SegmentEntry(start, limit, type, privLvl))




