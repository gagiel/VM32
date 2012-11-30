
class CPUState(object):
	def __init__(self):
		#Segments
		self.CS = 0
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
		self.privLvl = 0
