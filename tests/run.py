#!/usr/bin/env python

import unittest

import MemoryTests

if __name__ == '__main__':
	testSuite = unittest.TestSuite()
	testLoader = unittest.defaultTestLoader

	testSuite.addTests([
		testLoader.loadTestsFromModule(MemoryTests)
	])

	unittest.TextTestRunner().run(testSuite)
