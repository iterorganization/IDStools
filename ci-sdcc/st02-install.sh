#!/bin/bash
# Bamboo CI script to build actor and run standalone program
# Execute script from root directory

source ./ci-sdcc/st00-header.sh

# Note Disable set -e option when using on local as it will exit the shell on error
if [[ "$(uname -n)" == *"bamboo"* ]]; then
    set -e -u -o pipefail
fi
#remove previously created environment
VIRTUALENV_DIR=virtualenvdir
if [ -d "$VIRTUALENV_DIR" ]; then
    rm -r "$VIRTUALENV_DIR"
fi

# create virtual env
python3 -m venv "$VIRTUALENV_DIR"

# activate virtual env
source "$VIRTUALENV_DIR"/bin/activate
# install created wheel package
pip install dist/*.whl

set +x
deactivate

echo "Done"
