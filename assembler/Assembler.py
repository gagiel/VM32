import logging
from collections import defaultdict

from Exceptions import AssemblyError, InstructionError
from CommonTypes import SegAddr
from Parser import Number, Id, String, MemRef, DoubleMemRef, Instruction, Directive, LabelDef

from .Parser import Parser
from .ObjectFile import ObjectFile

from Instructions import doesInstructionExist, getInstructionLength, assembleInstruction

class Assembler(object):
	def __init__(self):
		self.parser = Parser()
		self.logger = logging.getLogger('Assembler')

	def assemble(self, input):
		parsed = self.parser.parse(input)
		self.logger.debug("Parsed tokens: %s", parsed)

		symtab, addr_imf = self._computeAddresses(parsed)
		self.logger.debug("Symbol table: %s", symtab)
		self.logger.debug("Line addresses: %s", addr_imf)

		objectfile = self._assembleCode(symtab, addr_imf)
		self.logger.debug("Assembled object file: %s", objectfile)

		return objectfile

	def _computeAddresses(self, imf):
		""" Pass 1 of the assembler creates a global symbol table
			and a list of tupels: Each line in the input gets a
			segment and the address of this line inside the segment.
			All .segment directives are stripped in this pass
		"""

		self.logger.debug("Assembler Pass 1: Computing addresses")

		#symbol table
		symtab = {}

		#pairs of lines and addresses inside a segment
		addr_imf = []

		#current address counters for each encountered segment
		seg_addr = {}

		#current segment selected via .segment directive
		cur_seg = None

		for line in imf:
			#Get current segment address for this line
			if not cur_seg:
				if not (isinstance(line, Directive) and line.name == '.segment' and not line.label):
					self._no_segment_error(line.lineno)
			else:
				saddr = SegAddr(cur_seg, seg_addr[cur_seg])

			#If line has a label, add it to symbol table with current address
			if line.label:
				if line.label in symtab:
					self._assembly_error("label '%s' already defined" % line.label, line. lineno)

				symtab[line.label] = saddr

			#If line is an instruction, get its length and calculate next address
			if isinstance(line, Instruction):
				if line.name is None:
					pass
				elif doesInstructionExist(line.name):
					addr_imf.append((saddr, line))
					seg_addr[cur_seg] += getInstructionLength(line.name)
				else:
					self._assembly_error("Unknown instruction: '%s" % line.name, line.lineno)

			#If current line is a directive handle them accordingly
			elif isinstance(line, Directive):
				if cur_seg and line.name != '.segment':
					addr_imf.append((saddr, line))

				if line.name == '.segment':
					self._validate_args(line, [Id])
					cur_seg = line.args[0].id
					if not cur_seg in seg_addr:
						seg_addr[cur_seg] = 0
				elif line.name == '.word':
					seg_addr[cur_seg] += len(line.args) * 4
				elif line.name == '.alloc':
					self._validate_args(line, [Number])
					seg_addr[cur_seg] = seg_addr[cur_seg] + int(line.args[0].val)
				elif line.name == '.string':
					self._validate_args(line, [String])
					seg_addr[cur_seg] = seg_addr[cur_seg] + len(line.args[0].val) + 1
			
			#Unknown line type encountered, should not happen due to parsing
			else:
				self._assembly_error("Bad Assembly", line.lineno)

		return symtab, addr_imf

	def _assembleCode(self, symtab, addr_imf):
		self.logger.debug("Assembler Pass 2: Assembling code")

		defines = {}

		seg_data = defaultdict(list)

		export_table = []
		import_table = []
		reloc_table = []

		for addr, line in addr_imf:
			if isinstance(line, Instruction):
				assert len(seg_data[addr.segment]) == addr.offset

				try:
					instructions = assembleInstruction(line.name, line.args, addr, symtab, defines)
				except InstructionError,e:
					self._assembly_error(e, line.lineno)

				for instr in instructions:
					offset = len(seg_data[addr.segment])

					#if instr.import_req:
					#	type, symbol = instr.import_req
					#	import_table.append(ImportEntry(
					#		import_symbol=symbol,
					#		type=type,
					#		addr=SegAddr(addr.segment, offset)))

					#if instr.reloc_req:
					#	type, sefment = instr.reloc_req
					#	reloc_table.append(RelocEntry(
					#		reloc_segment=segment,
					#		type=type,
					#		addr=SegAddr(addr.segment, offset)))

					seg_data[addr.segment].extend(list(instr.op))
			
			elif isinstance(line, Directive):
				pass

			else:
				self._assembly_error("Bad Assembly", line.lineno)

		return ObjectFile.fromAssembler(
			seg_data=seg_data,
			export_table=export_table,
			import_table=import_table,
			reloc_table=reloc_table)

	def _validate_args(self, line, expected_arguments):
		if len(expected_arguments) != len(line.args):
			self._assembly_error("%s -- %s argument(s) expected" % (line.name, len(expected_arguments)), line.lineno)

		for i, expected_type in enumerate(expected_arguments):
			if not isinstance(line.args[i], expected_type):
				self._assembly_error("%s -- argument '%s' of unexpected type" % (line.name, line.args[i]), line.lineno)

	def _no_segment_error(self, lineno):
		self._assembly_error("A segment must be defined before this line", lineno)

	def _assembly_error(self, msg, lineno):
		raise AssemblyError("%s (at line %s)" % (msg, lineno))
