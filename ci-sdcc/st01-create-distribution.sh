#!/bin/bash
# Bamboo CI script to create source distribution and whl package
# Execute script from root directory

# setup environment
source ./ci-sdcc/st00-header.sh

if [[ "$(uname -n)" == *"bamboo"* ]]; then
    set -e -u -o pipefail
fi

if [ -d "dist" ]; then
    rm -rf "dist"
fi

VIRTUALENV_DIR=virtualenvdir
if [ -d "$VIRTUALENV_DIR" ]; then
    rm -r "$VIRTUALENV_DIR"
fi

# create virtual env
python3 -m venv "$VIRTUALENV_DIR"
# activate virtual env
source "$VIRTUALENV_DIR"/bin/activate
pip install build

# Debuggging:
# create a source distribution
python -m build --sdist
# create wheel compiled version of the package
python -m build --wheel
deactivate

echo "Done"
