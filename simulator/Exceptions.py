class SimulatorError(Exception): pass
class CPUStateError(Exception): pass
class CPUStateSegTblFaultyError(Exception): pass

class CPUSegmentViolationException(Exception):
	def __init__(self, segment, offset):
		self.segment = segment
		self.offset = offset
