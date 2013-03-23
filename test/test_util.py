import unittest
import doctest
import crab.util.string

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(crab.util.string))
    return tests
