#!/usr/bin/env python

import sys

from simulator import Memory

def main(argc, argv):
	print("Hello!")
	m = Memory.Memory([0])

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
