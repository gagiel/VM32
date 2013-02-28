import struct
import logging

#total memory size
MEMORY_SIZE = 4*1024*1024*1024

class MemoryException(Exception): pass
class MemoryAddressOutOfBoundsException(MemoryException): pass
class MemoryDataOutOfBoundsException(MemoryException): pass

class Memory(object):
	def __init__(self):
		self.memory = {}
		self.logger = logging.getLogger('Memory')
		self.logger.debug("Creating Memory with size %d KiB", MEMORY_SIZE/1024)

	@classmethod
	def createFromBinaryString(cls, memstr):
		if len(memstr) % 4 != 0:
			logger.error("The length of the memory image has to be a multiple of 4 Bytes")

		instance = Memory()
		for i in range(len(memstr) / 4):
			instance.memory[i] = struct.unpack("<I", memstr[i*4:(i*4)+4])[0]

		return instance

	def writeBlob(self, address, blob):
		for word in blob:
			self.memory[address] = word
			address += 1

	def writeWord(self, address, word):
		#self.logger.debug("Writing value 0x%x to address 0x%x", word, address)
		if address >= MEMORY_SIZE or address < 0:
			raise MemoryAddressOutOfBoundsException("Address {0} for write operation out of bounds".format(address))
		
		if(word > 0xFFFFFFFF or word < 0):
			raise MemoryDataOutOfBoundsException("Data {0} for write operation at address {1} out of bounds".format(word, address))

		self.memory[address] = word

	def readWord(self, address):
		#self.logger.debug("Reading from address 0x%x", address)
		if address >= MEMORY_SIZE or address < 0:
			raise MemoryAddressOutOfBoundsException("Address {0} for read operation out of bounds".format(address))
		
		if address in self.memory:
			return self.memory[address]
		else:
			return 0xFFFFFFFF

	def readRange(self, address, length):
		values = []
		for i in range(length):
			values.append(self.readWord(address + i))

		return values

	def readBinary(self, address):
		return struct.pack("<I", self.readWord(address))

	def readRangeBinary(self, address, length):
		values = []
		for i in range(length):
			values.append(self.readBinary(address + i))

		return values

	#def readInstruction(self, address):
	#	#TODO: Alignment to 64 bit? i.e. address dividable by 2 here?
	#	#little endian
	#	return self.readWord(address) | (self.readWord(address+1) << 32)
