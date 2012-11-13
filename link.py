#!/usr/bin/env python

import sys
import argparse
import logging
import pickle

from linker.Linker import Linker

def main(argc, argv):
	parser = argparse.ArgumentParser(description='VM32 Linker')
	parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Display debug information (DEBUG)')

	parser.add_argument('-o', '--output', action='store', nargs=1, dest='outFileName', help='Output filename', metavar="outFileName", required=False)
	parser.add_argument('inputFiles', metavar='input file', nargs='+', type=argparse.FileType('r'), help='Input files to link into an executable')

	arguments = parser.parse_args(argv[1:])
	
	#enable logging
	if arguments.debug:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger('Linker Frontend')

	try:
		#create and truncate output file
		if arguments.outFileName != None:
			outputFile = open(arguments.outFileName[0], 'w+')
		else:
			outputFile = open('out.bin', 'w+')
		logger.debug("Writing to file %s", outputFile.name)

		#load object files
		objectFiles = []
		for file in arguments.inputFiles:
			logger.debug("Loading object files %s" % file)
			objectFiles.append(pickle.load(file))
		
		linker = Linker()
		image = linker.link(objectFiles)

		binaryString = ""
		for word in image:
			binaryString += word

		outputFile.write(binaryString)
		outputFile.close()

	except IOError, e:
		logger.error(e)

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
