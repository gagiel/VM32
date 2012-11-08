#!/usr/bin/env python

import unittest

import MemoryTests
import LexerTests
import ParserTests

if __name__ == '__main__':
	testSuite = unittest.TestSuite()
	testLoader = unittest.defaultTestLoader

	testSuite.addTests([
		testLoader.loadTestsFromModule(MemoryTests),
		testLoader.loadTestsFromModule(LexerTests),
		testLoader.loadTestsFromModule(ParserTests),
	])

	unittest.TextTestRunner().run(testSuite)
