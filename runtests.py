#!/usr/bin/env python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from moxie.tests import main
result = main()
if not result.wasSuccessful():
    sys.exit(1)
