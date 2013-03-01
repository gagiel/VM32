#!/usr/bin/env python

import sys
import argparse
import logging
import pickle

from linker.Linker import Linker

def main(argc, argv):
	parser = argparse.ArgumentParser(description='VM32 Linker')
	parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Display debug information (DEBUG)')
	parser.add_argument('-m', '--map', action='store', nargs=1, dest='mapFileName', help='Map filename', metavar='mapFileName', required=False)

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
		#load object files
		objectFiles = []
		for file in arguments.inputFiles:
			logger.debug("Loading object files %s" % file)
			objectFiles.append(pickle.load(file))
		
		linker = Linker()
		image, symboltables = linker.link(objectFiles)

		#build a binary string out of the list
		binaryString = ""
		for word in image:
			binaryString += word

		#create and truncate output file
		if arguments.outFileName != None:
			outputFile = open(arguments.outFileName[0], 'w+')
		else:
			outputFile = open('out.bin', 'w+')
		logger.debug("Writing to file %s", outputFile.name)

		#write image to file
		outputFile.write(binaryString)
		outputFile.close()

		#write the map file
		if arguments.mapFileName != None:
			mapFile = open(arguments.mapFileName[0], 'w+')
			for idx, sourceFile in enumerate(arguments.inputFiles):
				mapFile.write("#%s\n" % sourceFile.name)
				for symbol in symboltables[idx].iterkeys():
					mapFile.write("%s %x\n" % (symbol, symboltables[idx][symbol]))
				mapFile.write("\n")
			mapFile.close()

	except IOError, e:
		logger.error(e)
		sys.exit(-1)
	except Exception, e:
		logger.error(e)
		sys.exit(-1)

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
