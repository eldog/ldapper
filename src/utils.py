# This should very much be its own proper package
import os
import sys

def abspath(path):
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), path))

