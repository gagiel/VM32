#!/usr/bin/env python

import sys
import argparse
import logging

from simulator.CPU import CPU

def main(argc, argv):
	parser = argparse.ArgumentParser(description='VM32 Linker')
	parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Display debug information (DEBUG)')

	parser.add_argument('memoryImage', metavar='memory image', type=argparse.FileType('r'), help='Image to be loaded into the system memory')

	arguments = parser.parse_args(argv[1:])
	
	#enable logging
	if arguments.debug:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger('Simulator Driver')

	#logger.debug("Preparing memory image")
	#memoryImage = arguments.memoryImage.read()
	#if len(memoryImage) % 4 != 0:
	#	logger.error("The length of the memory image has to be a multiple of 4 Bytes")

	#wordifiedMemory = []
	#for i in range(len(memoryImage) / 4):
	#	wordifiedMemory.append(memoryImage[i*4:(i*4)+4])

	logger.debug("Creating CPU")
	cpu = CPU(arguments.memoryImage.read())

	while cpu.doSimulationStep():
		pass

	logger.info("Simulation ended")

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
