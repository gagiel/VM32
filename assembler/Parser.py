#taken from http://code.google.com/p/luz-cpu/source/browse/luz_asm_sim/lib/asmlib/asmparser.py

import ply.yacc as yacc
from Lexer import Lexer
from collections import namedtuple

from Exceptions import ParseError

Number = namedtuple('Number', 'val')
Id = namedtuple('Id', 'id')
Register = namedtuple('Register', 'reg')
SpecialRegister = namedtuple('SpecialRegister', 'reg')
String = namedtuple('String', 'val')
MemRef = namedtuple('Memref', 'offset id segment')
DoubleMemRef = namedtuple('DoubleMemRef', 'offset id segment')
Instruction = namedtuple('Instruction', 'label name args lineno')
Directive = namedtuple('Directive', 'label name args lineno')
LabelDef = namedtuple('LabelDef', 'label lineno')

class Parser(object):
	def __init__(self):
		self.lexer = Lexer(error_callback=self._lexer_error)
		self.tokens = self.lexer.tokens

		self.parser = yacc.yacc(module=self)

	def parse(self, text):
		self.lexer.reset()
		return self.parser.parse(text + "\n", lexer=self.lexer)

	def _lexer_error(self, errorMsg):
		raise ParseError(errorMsg)

	#Grammar
	def p_asm_file(self, p):
		''' asm_file    : asm_line
						| asm_file asm_line
		'''
		# skip empty lines
		if len(p) >= 3:
			p[0] = p[1] + [p[2]] if p[2] else p[1]
		else:
			p[0] = [p[1]] if p[1] else []
	
	def p_asm_line_1(self, p):
		''' asm_line    : empty_line 
						| directive NEWLINE 
						| instruction NEWLINE
		'''
		p[0] = p[1]
	
	def p_asm_line_2(self, p):
		''' asm_line : label_def NEWLINE '''
		p[0] = Instruction(
			label=p[1].label,
			name=None,
			args=[],
			lineno=p[1].lineno)
	
	def p_empty_line(self, p):
		''' empty_line : NEWLINE '''
		p[0] = None
	
	def p_directive_1(self, p):
		''' directive : label_def DIRECTIVE arguments_opt '''
		p[0] = Directive(
			label=p[1].label,
			name=p[2],
			args=p[3],
			lineno=p.lineno(2))

	def p_directive_2(self, p):
		''' directive : DIRECTIVE arguments_opt '''
		p[0] = Directive(
			label=None,
			name=p[1],
			args=p[2],
			lineno=p.lineno(1))    
	
	def p_instruction_1(self, p):
		''' instruction     : label_def ID arguments_opt '''
		p[0] = Instruction(
			label=p[1].label,
			name=p[2],
			args=p[3],
			lineno=p.lineno(2))
	
	def p_instruction_2(self, p):
		''' instruction     : ID arguments_opt '''
		p[0] = Instruction(
			label=None,
			name=p[1],
			args=p[2],
			lineno=p.lineno(1))
	
	def p_label_def(self, p):
		''' label_def   : ID COLON '''
		p[0] = LabelDef(p[1], p.lineno(1))
	
	def p_arguments_opt(self, p):
		''' arguments_opt   : arguments
							|
		'''
		p[0] = p[1] if len(p) >= 2 else []
	
	def p_arguments_1(self, p):
		''' arguments   : argument '''
		p[0] = [p[1]]
	
	def p_arguments_2(self, p):
		''' arguments   : arguments COMMA argument '''
		p[0] = p[1] + [(p[3])]
	
	def p_argument_1(self, p):
		''' argument    : REGISTER '''
		p[0] = Register(p[1])

	def p_argument_2(self, p):
		''' argument    : ID '''
		p[0] = Id(p[1])

	def p_argument_3(self, p):
		''' argument    : SPECIALREGISTER '''
		p[0] = SpecialRegister(p[1])
		
	def p_argument_4(self, p):
		''' argument    : STRING '''
		p[0] = String(p[1])
	
	def p_argument_5(self, p):
		''' argument    : number '''
		p[0] = p[1]

	def p_argument_6(self, p):
		''' argument    : LPAREN numorid RPAREN
		'''
		p[0] = MemRef(offset=None, id=p[2], segment="ds")

	def p_argument_7(self, p):
		''' argument    : LSQBRACKET numorid RSQBRACKET
		'''
		p[0] = DoubleMemRef(offset=None, id=p[2], segment="ds")

	def p_argument_8(self, p):
		''' argument    : REGISTER LPAREN numorid RPAREN
		'''
		p[0] = MemRef(offset=Register(p[1]), id=p[3], segment="ds")

	def p_argument_9(self, p):
		''' argument    : REGISTER LSQBRACKET numorid RSQBRACKET
		'''
		p[0] = DoubleMemRef(offset=Register(p[1]), id=p[3], segment="ds")

	def p_argument_10(self, p):
		''' argument    : ID COLON REGISTER LPAREN numorid RPAREN
		'''
		p[0] = MemRef(offset=Register(p[3]), id=p[5], segment=p[1])

	def p_argument_11(self, p):
		''' argument    : ID COLON REGISTER LSQBRACKET numorid RSQBRACKET
		'''
		p[0] = DoubleMemRef(offset=Register(p[3]), id=p[5], segment=p[1])

	def p_argument_12(self, p):
		''' argument    : ID COLON LPAREN numorid RPAREN
		'''
		p[0] = MemRef(offset=None, id=p[4], segment=p[1])

	def p_argument_13(self, p):
		''' argument    : ID COLON LSQBRACKET numorid RSQBRACKET
		'''
		p[0] = DoubleMemRef(offset=None, id=p[4], segment=p[1])

	def p_memref_arg_num_or_id(self, p):
		''' numorid  : number
						| ID
		'''
		if isinstance(p[1], Number):
			p[0] = p[1]
		else:
			p[0] = Id(p[1])

	def p_number(self, p):
		''' number  : DEC
					| HEX
		'''
		#FIXME: convert to 2s complement?
		p[0] = Number(p[1])
	
	def p_error(self, p):
		next_t = yacc.token()
		raise ParseError("invalid code before %s (at line %s)" % (repr(next_t.value), next_t.lineno))
