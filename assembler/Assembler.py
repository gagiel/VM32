import logging
import struct
from collections import defaultdict

from Exceptions import AssemblyError, InstructionError
from CommonTypes import SegAddr
from Parser import Number, Id, String, MemRef, DoubleMemRef, Instruction, Directive, LabelDef

from .Parser import Parser
from .ObjectFile import ObjectFile, ExportEntry, ImportEntry, RelocEntry

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
					seg_addr[cur_seg] += getInstructionLength(line.name, line.args)
				else:
					self._assembly_error("Unknown instruction: '%s" % line.name, line.lineno)

			#If current line is a directive handle them accordingly
			elif isinstance(line, Directive):
				if cur_seg and line.name != '.segment':
					addr_imf.append((saddr, line))

				#create a new segment if it is unknown at this point
				if line.name == '.segment':
					self._validate_args(line, [Id])
					cur_seg = line.args[0].id
					if not cur_seg in seg_addr:
						seg_addr[cur_seg] = 0

				#reserve space in the current segment for initialized data
				elif line.name == '.word':
					seg_addr[cur_seg] += len(line.args)

				#reserve space in the current segment for zero-initialized data
				elif line.name == '.alloc':
					self._validate_args(line, [Number])
					seg_addr[cur_seg] = seg_addr[cur_seg] + int(line.args[0].val)

				#reserve space in the current segment for a string
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
		privilegeLevel = 0

		seg_data = defaultdict(list)

		export_table = []
		import_table = []
		reloc_table = []

		for addr, line in addr_imf:
			#assemble an instruction
			if isinstance(line, Instruction):
				assert len(seg_data[addr.segment]) == addr.offset

				try:
					#assemble the instruction and generate import and relocation information
					instruction = assembleInstruction(line.name, line.args, addr, symtab, defines, privilegeLevel)

					#get the offset where this instruction is placed at
					offset = len(seg_data[addr.segment])

					#add relocation and import metainformation to linker information tables
					for arg in instruction.arguments:
						if arg["import"] != None:
							import_table.append(ImportEntry(
								import_symbol=arg["import"],
								addr=SegAddr(addr.segment, offset+arg["offsetInInstruction"])))

						if arg["relocation"] != None:
							reloc_table.append(RelocEntry(
								reloc_segment=arg["relocation"],
								addr=SegAddr(addr.segment, offset+arg["offsetInInstruction"])))

					#add instruction to current segment
					seg_data[addr.segment].extend(list(instruction.op))
				except InstructionError,e:
					self._assembly_error(e, line.lineno)

			#handle a directive
			elif isinstance(line, Directive):
				if line.name == '.define':
					self._validate_args(line, [Id, Number])
					defines[line.args[0].id] = line.args[1].val

				elif line.name == '.privlvl':
					self._validate_args(line, [Number])
					if line.args[0].val < 0 or line.args[0].val > 255:
						self._assembly_error(".privlvl -- argument needs to be a number between 0 and 255", line.lineno)
					privilegeLevel = line.args[0].val

				#define a symbol as exported
				elif line.name == '.global':
					self._validate_args(line, [Id])
					symbol_name = line.args[0].id

					if symbol_name in symtab:
						export_table.append(ExportEntry(
							export_symbol=symbol_name,
							addr=symtab[symbol_name]))
					else:
						self._assembly_error('.global defines an unknown label %s' % symbol_name, line.lineno)

				#allocate n words of space and initialize them with zeros
				elif line.name == '.alloc':
					num = line.args[0].val
					for i in range(num):
						seg_data[addr.segment].extend([struct.pack("<I", 0)])

				#allocate n words of space and initialize them with the values in the arguments
				elif line.name == '.word':
					data = []

					for i, word_arg in enumerate(line.args):
						if isinstance(word_arg, Number):
							try:
								data.extend([struct.pack("<I", word_arg.val)])
							except:
								self._assembly_error(".word -- argument %s is not a valid 32 bit word" % (i + 1,), line.lineno)
						elif isinstance(word_arg, Id):
							if word_arg.id in defines:
								data.extend([struct.pack("<I", defines[word_arg.id])])
							elif word_arg.id in symtab:
								data.extend([struct.pack("<I", symtab[word_arg.id].offset)])
								reloc_table.append(RelocEntry(
									reloc_segment=symtab[word_arg.id].segment,
									addr=SegAddr(addr.segment, len(seg_data[addr.segment]) + i)))
							else:
								data.extend([struct.pack("<I", 0)])
								import_table.append(ImportEntry(
									import_symbol=word_arg.id,
									addr=SegAddr(addr.segment, len(seg_data[addr.segment]) + i)))
						else:
							self._assembly_error(".word -- argument %s is not a valid word" % (i + 1,), line.lineno)

					seg_data[addr.segment].extend(data)

				#allocate space for a string and zero terminate it
				elif line.name == '.string':
					data = []
					for c in line.args[0].val:
						data.extend([chr(ord(c)) + "\x00\x00\x00"])
					data.extend(["\x00\x00\x00\x00"])
					seg_data[addr.segment].extend(data)

				else:
					#.segment directives should have been stripped in the first assembler pass
					assert line.name != '.segment'
					self._assembly_error('Unknown directive %s' % line.name, line.lineno)

			else:
				self._assembly_error("Bad Assembly", line.lineno)

		#create an objectfile containing all segments with their data, import-, export- and relocation tables
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
