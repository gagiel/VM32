import ply.lex as lex
import re

#LEX Example: http://www.dabeaz.com/ply/ply.html#ply_nn4

class Lexer(object):
	def __init__(self, error_callback):
		self._error_callback = error_callback
		self.lexer = lex.lex(object=self)

	def input(self, text):
		self.lexer.input(text)

	def token(self):
		return self.lexer.token()

	def reset(self):
		self.lexer.lineno = 1

	tokens = (
		'ID', 'DIRECTIVE', 'REGISTER', 'SPECIALREGISTER',
		'DEC', 'HEX', 'STRING',
		'COLON', 'COMMA', 'RPAREN', 'LPAREN',
		'LSQBRACKET', 'RSQBRACKET',
		'NEWLINE'
	)

	t_COLON = r':'
	t_COMMA = r','
	t_RPAREN = r'\)'
	t_LPAREN = r'\('
	t_LSQBRACKET = r'\['
	t_RSQBRACKET = r'\]'

	t_ignore = ' \t'

	#identifier may start with characters, underscore or dollar
	#and the following chars may be alphanumeric or _
	#at least one character long
	def t_REGISTER(self, t):
		r'(r|R)[0-9]+'
		t.value = int(t.value.lower()[1:])
		return t

	def t_SPECIALREGISTER(self, t):
		r'(cr_|CR_)[a-zA-Z]+'
		t.value = t.value.lower()[3:]
		return t

	def t_ID(self, t):
		r'[a-zA-Z_\$][0-9a-zA-Z_]*'
		t.value = t.value.lower()
		return t

	def t_DIRECTIVE(self, t):
		r'\.[0-9a-zA-Z_]*'
		t.value = t.value.lower()
		return t

	def t_HEX(self, t):
		r'0[xX][0-9a-fA-F]+'
		t.value = int(t.value, 16)
		return t

	def t_DEC(self, t):
		r'\d+'
		t.value = int(t.value, 10)
		return t

	#\, ", newline and tab can be escaped in a string
	def t_STRING(self, t):
		r'"([^"\\\n]|\\["\\nt])*"'
		t.value = t.value[1:-1].decode('string_escape')
		return t

	def t_NEWLINE(self, t):
		r'\n'
		t.lexer.lineno += t.value.count('\n')
		return t

	def t_COMMENT(self, t):
		r'\#.*'
		pass

	def t_error(self, t):
		self._error_callback("Illegal character '%s' at line %s" % (t.value[0], t.lineno))
		t.lexer.skip(1)
