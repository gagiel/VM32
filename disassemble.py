#!/usr/bin/env python

import sys
import argparse
import logging
#import pickle

from utils.Disassembler import Disassembler

def main(argc, argv):
	parser = argparse.ArgumentParser(description='VM32 Disassembler: The output may not be pretty, but this tool can be used to debug the assembler, linker and simulator itself')
	parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Display debug information (DEBUG)')

	parser.add_argument('inputFile', metavar='input file', type=argparse.FileType('r'), help='Input file to disassemble')

	arguments = parser.parse_args(argv[1:])
	
	#enable logging
	if arguments.debug:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger('Disassembler Frontend')

	try:
		#load object files
		logger.debug("Loading binary code from %s" % arguments.inputFile)
		binCode = arguments.inputFile.read()
		arguments.inputFile.close()

		disassembler = Disassembler()
		
		logger.debug("Starting disassembly...")
		text = disassembler.disassembleBinBlob(binCode)

		print text

	except IOError, e:
		logger.error(e)
		sys.exit(-1)
	#except Exception, e:
	#	logger.error(e)
	#	sys.exit(-1)

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
