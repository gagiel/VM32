import unittest, sys
sys.path.insert(0, '.')

from assembler.Lexer import Lexer
from ply.lex import LexToken

lexTest = """.segment text
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
	SUB (R0), [R1]
	RETI
"""

class MemoryTest(unittest.TestCase):
	def setUp(self):
		self.lexer = Lexer(error_callback=self.fail)

	def assert_token(self, inputText, expectedToken):
		self.lexer.input(inputText)
		token = self.lexer.token()
		self.assertEqual(token.type, expectedToken[0])
		self.assertEqual(token.value, expectedToken[1])

	def test_ID(self):
		self.assert_token('bla', ('ID', 'bla'))
		self.assert_token('bLa', ('ID', 'bla'))
		self.assert_token('_bLa', ('ID', '_bla'))
		self.assert_token('$b123a', ('ID', '$b123a'))

	def test_DIRECTIVE(self):
		self.assert_token('.bla', ('DIRECTIVE', '.bla'))
		self.assert_token('.bLa', ('DIRECTIVE', '.bla'))
		self.assert_token('._bLa', ('DIRECTIVE', '._bla'))
		self.assert_token('.b123a', ('DIRECTIVE', '.b123a'))

	def test_DEC(self):
		self.assert_token('12', ('DEC', 12))
		self.assert_token('012', ('DEC', 12))
		self.assert_token('-12', ('DEC', -12))

	def test_HEX(self):
		self.assert_token('0x12', ('HEX', 0x12))
		self.assert_token('0x012', ('HEX', 0x12))
		self.assert_token('0X12', ('HEX', 0x12))
		self.assert_token('-0x12', ('HEX', -0x12))

	def test_STRING(self):
		self.assert_token('"teststring"', ("STRING", "teststring"))
		self.assert_token(r'"testlinebreak\n"', ("STRING", "testlinebreak\n"))
		self.assert_token(r'"e\tsc\nap\\e\"d"', ("STRING", "e\tsc\nap\\e\"d"))
