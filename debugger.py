#!/usr/bin/env python

import sys
import os
import argparse
import logging
import struct
import cmd

from simulator.CPU import CPU
from utils.Disassembler import Disassembler

def main(argc, argv):
	parser = argparse.ArgumentParser(description='VM32 Debuuger')
	parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Display debug information (DEBUG)')

	parser.add_argument('memoryImage', metavar='memory image', type=argparse.FileType('r'), help='Image to be loaded into the system memory')

	arguments = parser.parse_args(argv[1:])
	
	#enable logging
	if arguments.debug:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)

	cpu = CPU(arguments.memoryImage.read())

	#history stuff, if it fails don't worry and carry on
	try:
		historyPath = os.path.expanduser("~/.vm32history")

		import readline
		def save_history(historyPath=historyPath):
			readline.write_history_file(historyPath)

		if os.path.exists(historyPath):
			readline.read_history_file(historyPath)

		import atexit
		atexit.register(save_history)
	except Exception:
		print "GNU readline support not available"

	DebuggerShell(cpu).cmdloop()

disassembler = Disassembler()

class DebuggerShell(cmd.Cmd):
	def __init__(self, cpu):
		cmd.Cmd.__init__(self)
		self.cpu = cpu
		self.prompt = "VM32> "
		self.breakpoints = []

	def do_del(self, line):
		try:
			index = parseArgs(line)[0]
			if index < len(self.breakpoints):
				self.breakpoints.pop(index)
			else:
				print "Argument out of bounds"
		except (ValueError, IndexError):
			print "Argument parsing failed"

	def do_break(self, line):
		try:
			addr = parseArgs(line)[0]
			self.breakpoints.append(addr)
		except (ValueError, IndexError):
			print "Argument parsing failed"

	def do_list(self, line):
		if len(self.breakpoints) == 0:
			print "No breakpoints"
		else:
			for (idx, bp) in enumerate(self.breakpoints):
				print "%d - 0x%x" % (idx, bp)

	def do_read(self, line):
		try:
			args = parseArgs(line)
			addr = args[0]
			length = 1
			if len(args) > 1:
				length = args[1]

			for i in range(length):
				sys.stdout.write("%08x " % self.cpu.memory.readWord(addr + i))
				
				if (i+1) % 4 == 0:
					print ""

			print ""

		except (ValueError, IndexError):
			print "Argument parsing failed"

	def do_write(self, line):
		try:
			args = parseArgs(line)
			addr = args[0]
			val = args[1]
			self.cpu.memory.writeWord(addr, val)

		except (ValueError, IndexError):
			print "Argument parsing failed"

	def do_stack(self, line):
		#FIXME: this is totally hacked
		try:
			addr = hex(self.cpu.state.SP)
			val = parseArgs(line)[0]
			self.do_read(addr + " " + str(val))
		except (ValueError, IndexError):
			print "Argument parsing failed"

	def do_reg(self, line):
		print self.cpu.state.getStringRepresentation()

	def do_step(self, line):
		if not self.cpu.doSimulationStep():
			print "CPU Simulation ended"
			return

		(text, consumedWords) = disassembleInstruction(self.cpu, self.cpu.state.IP)
		print text

	def do_disassemble(self, line):
		try:
			args = parseArgs(line)
			addr = args[0]
			count = 1
			if len(args) > 1:
				count = args[1]
			
			for i in range(count):
				(text, consumedWords) = disassembleInstruction(self.cpu, addr)

				print text
				addr += consumedWords

		except (ValueError, IndexError):
			print "Argument parsing failed"

	def do_continue(self, line):
		while True:
			try:
				if self.cpu.state.IP in self.breakpoints:
					print "Breakpoint hit at 0x%08x" % self.cpu.state.IP
					(text, consumedWords) = disassembleInstruction(self.cpu, self.cpu.state.IP)
					print text
					return

				if not self.cpu.doSimulationStep():
					print "CPU Simulation ended"
					return
			except KeyboardInterrupt:
				print "Breaking at 0x%08x" % self.cpu.state.IP
				return

	def do_reset(self, line):
		print "Resetting CPU"
		self.cpu.reset()

	def do_quit(self, line):
		return True

	def do_EOF(self, line):
		return True

def parseArgs(argstr):
	return map(transformInt, argstr.split())

def transformInt(str):
	if str.startswith("0x"):
		return int(str, 16)
	elif len(str) > 1 and str.startswith("0"):
		return int(str, 8)
	else:
		return int(str, 10)

def disassembleInstruction(cpu, addr):
	data = cpu.memory.readRangeBinary(addr, 3)
	(disassembled, consumedWords) = disassembler.disassembleInstructionWord(data)

	text = ""
	#print address
	text += ("0x%08x:\t" % addr)

	#print words in hexadecimal...
	for i in range(consumedWords):
		text += ("%08x " % struct.unpack("<I", data[i])[0])

	#... or insert tabs instead
	for i in range(3 - consumedWords):
		text += "\t "

	#print the disassembled instructuin
	text += "\t" + disassembled

	return (text, consumedWords)

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
