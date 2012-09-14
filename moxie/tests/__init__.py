import unittest

def main():
    # Run all TestCases
    suite = unittest.TestLoader().discover('moxie.tests')
    return unittest.TextTestRunner(verbosity=2).run(suite)
