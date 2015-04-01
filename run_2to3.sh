#!/bin/bash

if [ -a annotator-py2 ]; then
    echo "Exiting: directory annotator-py2 already exists."
    exit 1
fi

# We copy the old annotator classes to a py2 folder.
mv annotator annotator-py2
# Run 2to3 using the following options:
# -o sets output dir
# -W writes files even if none were changed
# -n specifies no backups
# Further documentation at:
# https://docs.python.org/2/library/2to3.html
2to3 -o annotator -W -n annotator-py2 > annotator-2to3.txt

# annotator-2to3.txt contains a log of changes made.

# We do the same with tests.
mv tests tests-py2
2to3 -o tests -W -n tests-py2 > tests-2to3.txt