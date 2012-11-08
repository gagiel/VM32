import unittest, sys
sys.path.insert(0, '.')

from assembler.Parser import Parser

test = r""".segment text
.global main

#here is a comment
main:
	mov r0, 1
	MOV R1, 20
	MOV R2, 0x1234
	MOV R3, -0x12
	CMP R1, R2
	JNZ R1,			R3
	MOV R1,    R2
	JMP main	#comment on end of line
	SUB 1(R0), 2[R1]
	ADD 0(R0), 20[R3]
	ADD 0(0), 53(0x20)
	RETI
	.ascii "String lalala"
"""

class MemoryTest(unittest.TestCase):
	def setUp(self):
		self.parser = Parser()

	def test_parse(self):
		print(self.parser.parse(test))
