from common.Opcodes import *
from Exceptions import CPUStateError, CPUStateSegTblFaultyError, CPUSegmentViolationException

from collections import namedtuple

SegmentEntry = namedtuple("SegmentEntry", ["start", "limit", "type", "privLvl"])
VmEntry = namedtuple("VmEntry", ["CS", "DS", "ES", "SS", "RS", "IP", "Flags", "privLvl"])

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

		#Instruction-Pointer
		self.IP = 0

		#Flags
		self.Flags = 0

		#Misc
		self.VmTbl = 0
		self.SegTbl = 0

		self.InVM = False
		self.VmID = 0

		self.Counter = 0
		self.Compare = 0
		self.Int = 0

		self.interruptPending = False

		self.privLvl = 0

		self.segments = []
		self.vms = []

	def getResultingInstructionAddress(self):
		#TODO: check if privLvl is not violated

		if len(self.segments) == 0:
			return self.IP
		else:
			#check if segment descriptor exists
			if len(self.segments) < self.CS:
				raise CPUSegmentViolationException(SEGMENT_CODE, self.IP)

			#check type of segment
			if self.segments[self.CS].type != SEGMENT_CODE:
				raise CPUSegmentViolationException(SEGMENT_CODE, self.IP)

			#check boundaries of segment
			if self.IP < self.segments[self.CS].start or self.IP > self.segments[self.CS].limit:
				raise CPUSegmentViolationException(SEGMENT_CODE, self.IP)

			return self.IP

	def getResultingCodeAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			#check if segment descriptor exists
			if len(self.segments) < self.CS:
				raise CPUSegmentViolationException(SEGMENT_CODE, offset)

			#check type of segment
			if self.segments[self.CS].type != SEGMENT_CODE:
				raise CPUSegmentViolationException(SEGMENT_CODE, offset)

			#check boundaries of segment
			if offset < self.segments[self.CS].start or offset > self.segments[self.CS].limit:
				raise CPUSegmentViolationException(SEGMENT_CODE, offset)

			return offset

	def getResultingInterruptAddress(self):
		if len(self.segments) == 0:
			return 0x0
		else:
			return self.segments[self.CS].start

	def getResultingDataAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			#check if segment descriptor exists
			if len(self.segments) < self.DS:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			#check type of segment
			if self.segments[self.DS].type != SEGMENT_DATA:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			#check boundaries of segment
			if offset < self.segments[self.DS].start or offset > self.segments[self.DS].limit:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			return offset

	def getResultingExtraAddress(self, offset):
		if len(self.segments) == 0:
			return offset
		else:
			#check if segment descriptor exists
			if len(self.segments) < self.ES:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			#check type of segment
			if self.segments[self.ES].type != SEGMENT_DATA:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			#check boundaries of segment
			if offset < self.segments[self.ES].start or offset > self.segments[self.ES].limit:
				raise CPUSegmentViolationException(SEGMENT_DATA, offset)

			return offset

	def getResultingStackAddress(self):
		if len(self.segments) == 0:
			return self.getRegister(30)
		else:
			sp = self.getRegister(30)
			
			#check if segment descriptor exists
			if len(self.segments) < self.SS:
				raise CPUSegmentViolationException(SEGMENT_STACK, sp)

			#check type of segment
			if self.segments[self.SS].type != SEGMENT_STACK:
				raise CPUSegmentViolationException(SEGMENT_STACK, sp)

			#check boundaries of segment
			if sp < self.segments[self.SS].start or sp > self.segments[self.SS].limit:
				raise CPUSegmentViolationException(SEGMENT_STACK, sp)

			return sp

	def getRegister(self, reg):
		if reg < 0 or reg > 30:
			raise CPUStateError("Can't access register smaller than 0 or bigger than 30")

		if len(self.segments) == 0:
			return self.memory.readWord(0x2000 + reg)
		else:
			#check if segment descriptor exists
			if len(self.segments) < self.RS:
				raise CPUSegmentViolationException(SEGMENT_REGISTER, reg)

			#check type of segment
			if self.segments[self.RS].type != SEGMENT_REGISTER:
				raise CPUSegmentViolationException(SEGMENT_REGISTER, reg)

			#read register from memory
			return self.memory.readWord(self.segments[self.RS].start + reg)

	def setRegister(self, reg, value):
		if reg < 0 or reg > 30:
			raise CPUStateError("Can't access register smaller than 0 or bigger than 30")

		if len(self.segments) == 0:
			self.memory.writeWord(0x2000 + reg, value)
		else:
			#check if segment descriptor exists
			if len(self.segments) < self.RS:
				raise CPUSegmentViolationException(SEGMENT_REGISTER, reg)

			#check type of segment
			if self.segments[self.RS].type != SEGMENT_REGISTER:
				raise CPUSegmentViolationException(SEGMENT_REGISTER, reg)

			#write register to memory
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

	def clearGreaterEqualFlag(self):
		self.Flags &= ~(1<<1)

	def getGreaterEqualFlag(self):
		return (self.Flags & (1<<1)) != 0

	def decrementStackPointer(self):
		#TODO check segment limits

		sp = self.getRegister(30)
		sp -= 1
		sp &= 0xFFFFFFFF
		self.setRegister(30, sp)

	def incrementStackPointer(self):
		#TODO check segment limits
		
		sp = self.getRegister(30)
		sp += 1
		sp &= 0xFFFFFFFF
		self.setRegister(30, sp)

	def getSpecialRegister(self, index):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		if index == SPECIALREG_SEGTBL:
			return self.SegTbl
		elif index == SPECIALREG_VMTBL:
			return self.VmTbl
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
		elif index == SPECIALREG_COUNTER:
			return self.Counter
		elif index == SPECIALREG_COMPARE:
			return self.Compare
		elif index == SPECIALREG_INT:
			return self.Int
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")
		

	def setSpecialRegister(self, index, value):
		if index < 0 or index > len(SPECIALREGS):
			raise CPUStateError("Special Register index out of bounds")

		#FIXME: typen von segmenten checken

		if index == SPECIALREG_SEGTBL:
			self.SegTbl = value
			self._parseNewSegTbl()
		elif index == SPECIALREG_VMTBL:
			self.VmTbl = value
			self._parseNewVmTbl()
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
		elif index == SPECIALREG_COUNTER:
			self.Counter = value
		elif index == SPECIALREG_COMPARE:
			self.Compare = value
		elif index == SPECIALREG_INT:
			self.Int = value
		else:
			raise CPUStateError("Don't know how to handle special register index - this is a bug!")

	def handleHardwareTimerTick(self):
		if self.isTimerEnabled():
			if self.Counter == self.Compare:
				self.deactivateTimer()
				self.Counter = 0
				self.interruptPending = True
			else:
				self.Counter += 1

	def isTimerEnabled(self):
		return self.Int & 2 != 0

	def deactivateTimer(self):
		self.Int &= ~(2)

	def isInterruptEnabled(self):
		return self.Int & 1 != 0

	def isInterruptPending(self):
		return self.interruptPending

	def resetInterruptPending(self):
		self.interruptPending = False

	def enableInterrupts(self):
		self.Int |= 1

	def disableInterrupts(self):
		self.Int &= ~1

	#def setTimerExpired(self):
	#	self.Int |= 4

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

			if start == 0xFFFFFFFF and limit == 0xFFFFFFFF and type == 0xFFFFFFFF and privLvl == 0xFFFFFFFF:
				break

			if not type in SEGMENT_TYPES:
				raise CPUStateSegTblFaultyError("Unknown segment type encountered")

			if type == SEGMENT_REGISTER and (limit - start) != 31:
				raise CPUStateSegTblFaultyError("Register segments need to have a size of 31")

			self.segments.append(SegmentEntry(start, limit, type, privLvl))

	def _parseNewVmTbl(self):
		self.vms = []

		address = self.VmTbl
		while True:
			cs = self.memory.readWord(address)
			address += 1
			ds = self.memory.readWord(address)
			address += 1
			es = self.memory.readWord(address)
			address += 1
			ss = self.memory.readWord(address)
			address += 1
			rs = self.memory.readWord(address)
			address += 1
			ip = self.memory.readWord(address)
			address += 1
			flags = self.memory.readWord(address)
			address += 1
			privLvl = self.memory.readWord(address)
			address += 1

			if cs == 0xFFFFFFFF and ds == 0xFFFFFFFF and es == 0xFFFFFFFF and ss == 0xFFFFFFFF and rs == 0xFFFFFFFF and ip == 0xFFFFFFFF and flags == 0xFFFFFFFF and privLvl == 0xFFFFFFFF:
				break

			#FIXME: check if segment selectors are not out of bounds
			self.vms.append(VmEntry(cs, ds, es, ss, rs, ip, flags, privLvl))

	def saveHypervisorContext(self):
		#overwrite first entry (always hypervisor) with current state
		self.saveVmContext(0)

	def saveVmContext(self, vmid):
		#FIXME: error if vmtbl == 0

		address = self.VmTbl + 8*vmid
		self.memory.writeWord(address, self.CS)
		address += 1
		self.memory.writeWord(address, self.DS)
		address += 1
		self.memory.writeWord(address, self.ES)
		address += 1
		self.memory.writeWord(address, self.SS)
		address += 1
		self.memory.writeWord(address, self.RS)
		address += 1
		self.memory.writeWord(address, self.IP)
		address += 1
		self.memory.writeWord(address, self.Flags)
		address += 1
		self.memory.writeWord(address, self.privLvl)

		self._parseNewVmTbl()


	def setVmContext(self, vmid):
		#TODO: check index bounds of vmid
		self._parseNewVmTbl()

		self.InVM = True
		self.VmID = vmid
		self.CS = self.vms[vmid].CS
		self.DS = self.vms[vmid].DS
		self.ES = self.vms[vmid].ES
		self.RS = self.vms[vmid].RS
		self.SS = self.vms[vmid].SS
		self.IP = self.vms[vmid].IP
		self.Flags = self.vms[vmid].Flags
		self.privLvl = self.vms[vmid].privLvl
