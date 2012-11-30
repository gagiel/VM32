from .CPUState import CPUState
from .Memory import Memory

class CPU(object):
	def __init__(self, memoryImage):
		self.state = CPUState()
		self.memory = Memory(memoryImage)

	def doSimulationStep(self):
		pass
