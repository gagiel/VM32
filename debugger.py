#!/usr/bin/env python

import sys
import argparse
import logging
import struct

from simulator.CPU import CPU
from utils.Disassembler import Disassembler

disassembler = Disassembler()
breakpoints = []

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

	try:
		import readline
		readline.parse_and_bind("tab: complete")
		readline.set_completer(lambda text, state: commands.keys()[state])
	except:
		print "Readline support not available"

	lastCommand = None
	try:
		while True:
			line = raw_input('VM32> ')
			if line == "" and lastCommand == None:
				continue
			elif line != "":
				args = line.split(" ")
				lastCommand = args
				executeCommand(cpu, args)
			else:
				executeCommand(cpu, lastCommand)

	except (KeyboardInterrupt, EOFError):
		sys.exit(0)

	#while cpu.doSimulationStep():
	#	pass

def executeCommand(cpu, args):
	if not commands.has_key(args[0]):
		print "Unknown command: %s" % args[0]
		return

	if commands[args[0]][0] > len(args[1:]):
		print "Command %s expected %d arguments, %d supplied" % (args[0], commands[args[0]][0], len(args[1:]))
		return

	commands[args[0]][1](cpu, args[1:])

def doStep(cpu, args):
	data = cpu.memory.readRangeBinary(cpu.state.getResultingInstructionAddress(), 3)
	(disassembled, consumedWords) = disassembler.disassembleInstructionWord(data)

	text = ""
	#print address
	text += ("0x%08x:\t" % cpu.state.getResultingInstructionAddress())

	#print words in hexadecimal...
	for i in range(consumedWords):
		text += ("%08x " % struct.unpack("<I", data[i])[0])

	#... or insert tabs instead
	for i in range(3 - consumedWords):
		text += "\t "

	#print the disassembled instructuin
	text += "\t" + disassembled

	print text

	if not cpu.doSimulationStep():
		print "CPU Simulator ended, exiting"
		sys.exit(0)

def readMem(cpu, args):
	try:
		addr = int(args[0], 16)
		length = 1
		if len(args) > 1:
			length = int(args[1], 16)

		for i in range(length):
			sys.stdout.write("%08x " % cpu.memory.readWord(addr + i))
			
			if (i+1) % 4 == 0:
				print ""

		print ""

	except ValueError:
		print "Argument was not hex addr"

def writeMem(cpu, args):
	try:
		addr = int(args[0], 16)
		val = int(args[1], 16)
		cpu.memory.writeWord(addr, val)

	except ValueError:
		print "Argument was not hex addr"

def dumpStack(cpu, args):
	#FIXME: kind of hacky, but meh...
	addr = hex(cpu.state.getResultingStackAddress())
	val = args[0]
	readMem(cpu, [addr, val])

def showRegs(cpu, args):
	print cpu.state.getStringRepresentation()

def quit(cpu, args):
	sys.exit(0)

def help(cpu, args):
	for i in commands.iterkeys():
		print "%s - %s - %d Arguments" % (i, commands[i][2], commands[i][0])

def addBreakpoint(cpu, args):
	try:
		addr = int(args[0], 16)
		breakpoints.append(addr)
	except ValueError:
		print "Argument was not hex addr"

def listBreaks(cpu, args):
	for (idx, bp) in enumerate(breakpoints):
		print "%d - 0x%x" % (idx, bp)

def delBreakpoint(cpu, args):
	try:
		index = int(args[0])
		if index < len(breakpoints):
			breakpoints.remove[index]
		else:
			print "Argument out of bounds"
	except ValueError:
		print "Argument not an int"

commands = {
	"break": [1, addBreakpoint, "Adds a breakpoint for physical address x in hex"],
	"listBreaks": [0, listBreaks, "Lists all breakpoints"],
	"delBreak": [1, delBreakpoint, "Removes breakpoint x"],
	"step": [0, doStep, "Executes one simulation step"],
	"readMem": [1, readMem, "Reads memory"],
	"writeMem": [2, writeMem, "Writes memory"],
	"stack": [1, dumpStack, "Dumps n words from stack"],
	"regs": [0, showRegs, "Shows registers"],
	"quit": [0, quit, "Exits simulator"],
	"help": [0, help, "Displays this text"],
	"?": [0, help, "Displays this text"]
}

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
