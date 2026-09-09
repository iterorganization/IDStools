#!/bin/bash
# Bamboo CI script to test IDS tools on different toolchains
# Execute script from root directory
source ./ci-sdcc/st00-header.sh

# Note Disable set -e option when using on local as it will exit the shell on error
if [[ "$(uname -n)" == *"bamboo"* ]]; then
    set -e -u -o pipefail
fi

python -m venv "$ENVIRONEMNT_NAME"

. "$ENVIRONEMNT_NAME"/bin/activate
# Install and run linters
pip install --upgrade 'black >=24,<25' flake8 pylint

echo "---------------------------------------------------------------------"
echo "executing black"
black --check -l 120 idstools >black.log
black --check -l 120 idstools/scripts/bin/* >black_scripts.log
echo "---------------------------------------------------------------------"
echo "executing flake8"
flake8 --max-line-length=120 --ignore=E203,W503 idstools >flake8.log
# flake8 --max-line-length=120 --ignore=E203,W503 idstools/scripts/bin/ids* >flake8_idsscripts.log
# flake8 --max-line-length=120 --ignore=E203,W503 idstools/scripts/bin/plot* >flake8_plotscripts.log
# flake8 --max-line-length=120 --ignore=E203,W503 idstools/scripts/bin/print* >flake8_printscripts.log
# flake8 --max-line-length=120 --ignore=E203,W503 idstools/scripts/bin/db* >flake8_dbscripts.log
echo "---------------------------------------------------------------------"
# echo "executing pylint"
# pylint --max-line-length=120 -E ./idstools >pylint.log
echo "---------------------------------------------------------------------"
deactivate
rm -rf "$ENVIRONEMNT_NAME"
echo "Done"
