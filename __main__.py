
import os
import sys

try:
    from dbmind.components.index_advisor import main
except ImportError:
    libpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    sys.path.append(libpath)
    from index_advisor import main

main(sys.argv[1:])
