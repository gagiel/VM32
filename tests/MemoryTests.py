import unittest, sys
sys.path.insert(0, '.')

from simulator import Memory

class MemoryTest(unittest.TestCase):
	def setUp(self):
		self.memory = Memory.Memory([0, 0, 0x9ABCDEF0, 0x12345678])

	def test_readExistant(self):
		readVal = self.memory.readWord(0)
		self.assertEqual(readVal, 0)

	def test_readNonExistant(self):
		readVal = self.memory.readWord(0x1000)
		self.assertEqual(readVal, 0xFFFFFFFF)

	def test_readOutOfBounds(self):
		self.assertRaises(Memory.MemoryAddressOutOfBoundsException, self.memory.readWord, 0xFFFFFFFF+1)

	def test_write(self):
		self.memory.writeWord(1, 0xAA55AA55)
		readVal = self.memory.readWord(1)
		self.assertEqual(readVal, 0xAA55AA55)

	def test_writeOutOfBounds(self):
		self.assertRaises(Memory.MemoryAddressOutOfBoundsException, self.memory.writeWord, 0xFFFFFFFF+1, 0x12345678)

	def test_readInstruction(self):
		instruction = self.memory.readInstruction(2)
		self.assertEqual(instruction, 0x123456789ABCDEF0)
