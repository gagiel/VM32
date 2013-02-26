import logging
import struct
from simulator import Instructions
from common import Opcodes

class Disassembler(object):
	def __init__(self):
		self.logger = logging.getLogger('Disassembler')

	def disassembleBinBlob(self, binBlob):
		self.logger.debug("Starting to disassemble a byte-BLOB with 0x%x bytes lentgh", len(binBlob))

		#start by creating 4-byte words out of the BLOB
		words = []
		for i in range(len(binBlob) / 4):
			words.append(struct.pack("<I", struct.unpack("<I", binBlob[i*4:(i*4)+4])[0])) #FIXME: nicer way to do this?

		self.logger.debug("Converted the binary blob into the following words: %s", words)

		text = ""
		curIp = 0

		while len(words) > 0:
			(disassembled, consumedWords) = self.disassembleInstructionWord(words)

			#print address
			text += ("0x%08x:\t" % curIp)

			#print words in hexadecimal...
			for i in range(consumedWords):
				text += ("%08x " % struct.unpack("<I", words[i])[0])

			#... or insert tabs instead
			for i in range(3 - consumedWords):
				text += "\t "

			#print the disassembled instructuin
			text += "\t" + disassembled

			#check if opcode could be an ascii character
			rawIntWord = struct.unpack("<I", words[0])[0]
			if rawIntWord & 0xFFFFFF00 == 0 and rawIntWord & 0xFF < 128:
				text += "\t\t\t\t" + chr(rawIntWord & 0xFF)

			text += "\n"

			curIp += consumedWords
			words = words[consumedWords:]

		return text

	def disassembleInstructionWord(self, instructionWords):
		#get opcode word
		(opcode, privlvl, operandType1, operandType2) = struct.unpack("<BBBB", instructionWords[0])

		#decode operands
		registerOperand1 = operandType1 & 0x1F
		operandType1 = operandType1 >> 5

		registerOperand2 = operandType2 & 0x1F
		operandType2 = operandType2 >> 5
		
		#if opcode doesn't exist, bail
		if not Instructions.doesInstructionExist(opcode):
			return ("INV: 0x%x" % opcode, 1)

		#consume words according to opcode and operand types
		consumedWords = 1
		instructionName = Instructions.getInstructionName(opcode)

		argumentCount = Instructions.getArgumentCount(opcode)

		argument1Text = ""
		argument2Text = ""

		if argumentCount > 0 and len(instructionWords) > consumedWords:
			if operandType1 == Opcodes.PARAM_IMMEDIATE:
				argument1Text = "0x%x" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType1 == Opcodes.PARAM_REGISTER:
				argument1Text = "r%d" % registerOperand1

			elif operandType1 == Opcodes.PARAM_MEMORY_SINGLE_DS:
				regOffset = ""
				if registerOperand1 != 31:
					regOffset = "r%d" % registerOperand1
				argument1Text = "ds:"+regOffset+"(0x%x)" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType1 == Opcodes.PARAM_MEMORY_SINGLE_ES:
				regOffset = ""
				if registerOperand1 != 31:
					regOffset = "r%d" % registerOperand1
				argument1Text = "es:"+regOffset+"(0x%x)" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType1 == Opcodes.PARAM_MEMORY_DOUBLE_DS:
				regOffset = ""
				if registerOperand1 != 31:
					regOffset = "r%d" % registerOperand1
				argument1Text = "ds:"+regOffset+"[0x%x]" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType1 == Opcodes.PARAM_MEMORY_DOUBLE_ES:
				regOffset = ""
				if registerOperand1 != 31:
					regOffset = "r%d" % registerOperand1
				argument1Text = "es:"+regOffset+"[0x%x]" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType1 == Opcodes.PARAM_SPECIAL_REGISTER:
				argument1Text = Opcodes.SPECIALREGS_NAMES[registerOperand1]

			else:
				return ("INVALID OPERAND1 TYPE 0x%x FOR OPCODE: 0x%x" % (opcode, operandType1), 1)

		if argumentCount > 1 and len(instructionWords) > consumedWords:
			if operandType2 == Opcodes.PARAM_IMMEDIATE:
				argument2Text = "0x%x" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType2 == Opcodes.PARAM_REGISTER:
				argument2Text = "r%d" % registerOperand2

			elif operandType2 == Opcodes.PARAM_MEMORY_SINGLE_DS:
				regOffset = ""
				if registerOperand2 != 31:
					regOffset = "r%d" % registerOperand2
				argument2Text = "ds:"+regOffset+"(0x%x)" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType2 == Opcodes.PARAM_MEMORY_SINGLE_ES:
				regOffset = ""
				if registerOperand2 != 31:
					regOffset = "r%d" % registerOperand2
				argument2Text = "es:"+regOffset+"(0x%x)" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType2 == Opcodes.PARAM_MEMORY_DOUBLE_DS:
				regOffset = ""
				if registerOperand2 != 31:
					regOffset = "r%d" % registerOperand2
				argument2Text = "ds:"+regOffset+"[0x%x]" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType2 == Opcodes.PARAM_MEMORY_DOUBLE_ES:
				regOffset = ""
				if registerOperand2 != 31:
					regOffset = "r%d" % registerOperand2
				argument2Text = "es:"+regOffset+"[0x%x]" % struct.unpack("<I", instructionWords[consumedWords])
				consumedWords += 1

			elif operandType2 == Opcodes.PARAM_SPECIAL_REGISTER:
				argument2Text = Opcodes.SPECIALREGS_NAMES[registerOperand2]

			else:
				return ("INVALID OPERAND2 TYPE 0x%x FOR OPCODE: 0x%x" % (opcode, operandType2), 1)

		text =  instructionName

		if argument1Text != "":
			text += " " + argument1Text

		if argument2Text != "":
			text += ", " + argument2Text

		return (text, consumedWords)
