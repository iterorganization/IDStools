#!/bin/bash
# Bamboo CI script to test IDS tools on different toolchains
# Execute script from root directory
source ./ci-sdcc/st00-header.sh

if [[ "$(uname -n)" == *"bamboo"* ]]; then
    set -e -u -o pipefail
fi


VIRTUALENV_DIR=virtualenvdir
if [ -d "$VIRTUALENV_DIR" ]; then
    rm -r "$VIRTUALENV_DIR"
fi

# create virtual env
python3 -m venv "$VIRTUALENV_DIR"
# activate virtual env
source "$VIRTUALENV_DIR"/bin/activate
pip install --upgrade pip
pip install .
pip install coverage

# create logs directory
LOG_DIR="$PWD"/logs
mkdir -p "$LOG_DIR"

# run tests
coverage run --source=idstools -m pytest --junit-xml="$LOG_DIR"/test_report.xml idstools/test

# report
coverage report -i
deactivate
rm -rf "$VIRTUALENV_DIR"
echo "Done"
