#!/usr/bin/env python

import unittest

import MemoryTests
import LexerTests

if __name__ == '__main__':
	testSuite = unittest.TestSuite()
	testLoader = unittest.defaultTestLoader

	testSuite.addTests([
		testLoader.loadTestsFromModule(MemoryTests),
		testLoader.loadTestsFromModule(LexerTests),
	])

	unittest.TextTestRunner().run(testSuite)
