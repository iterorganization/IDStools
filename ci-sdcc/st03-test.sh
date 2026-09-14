#!/bin/bash
# Bamboo CI script to test IDS tools on different toolchains
# Execute script from root directory
source ./ci-sdcc/st00-header.sh

python -m venv "$ENVIRONEMNT_NAME"

. "$ENVIRONEMNT_NAME"/bin/activate

LOG_DIR="$PWD"/"$ENVIRONEMNT_NAME"/logs
mkdir -p "$LOG_DIR"

DB_DIR="$PWD"/"$ENVIRONEMNT_NAME"/db
mkdir -p "$DB_DIR"

#install packages
pip install --upgrade pip
pip install .
pip install packaging

PYTHON_VERSION=$(python --version)

# display versions
version_script=$(
    cat <<END
import numpy as np
import scipy
import matplotlib

print("NumPy version:", np.__version__)
print("SciPy version:", scipy.__version__)
print("Matplotlib version:", matplotlib.__version__)
END
)

echo "====================================================================="
python3 -c "$version_script"
echo "====================================================================="
#---------------------------------------------------------------------------
echo ""
echo ""
echo "====================================================================="
echo "Testing analysis scripts with $PYTHON_VERSION"
echo "====================================================================="
source ./tests/st03_test_analysis_scripts_with_uri.sh "$LOG_DIR" "$DB_DIR"
errstatus=$?
if [ $errstatus  -ne 0 ]; then
    echo "Error: st03_test_analysis_scripts_with_uri.sh failed."
    exit 1
fi

echo ""
echo ""
echo "====================================================================="
echo "Testing ids manipulation scripts with $PYTHON_VERSION"
echo "====================================================================="
source ./tests/st01_test_ids_scripts_with_uri.sh "$LOG_DIR" "$DB_DIR"
errstatus=$?
if [ $errstatus -ne 0 ]; then
    echo "Error: st01_test_ids_scripts_with_uri.sh failed."
    exit 1
fi

# ---------------------------------------------------------------------------
echo ""
echo ""
echo "====================================================================="
echo "Testing db scripts with $PYTHON_VERSION"
echo "====================================================================="
source ./tests/st02_test_db_scripts.sh "$LOG_DIR" "$DB_DIR"
errstatus=$?
if [ $errstatus -ne 0 ]; then
    echo "Error: st02_test_db_scripts.sh failed."
    exit 1
fi

# ---------------------------------------------------------------------------
echo ""
echo ""
echo "====================================================================="
echo "Testing scenario scripts with $PYTHON_VERSION"
echo "====================================================================="
source ./tests/st04_test_scenario_scripts.sh "$LOG_DIR" "$DB_DIR"
errstatus=$?
if [ $errstatus -ne 0 ]; then
    echo "Error: st04_test_scenario_scripts.sh failed."
    exit 1
fi

echo ""
echo ""
echo "====================================================================="
echo "Run pytest for functions testing with $PYTHON_VERSION"
echo "====================================================================="
pip install pytest
python -m pytest --junit-xml="$LOG_DIR"/test_report.xml idstools/test
errstatus=$?
if [ $errstatus -ne 0 ]; then
    echo "Error: pytest failed."
    exit 1
fi
echo "---------------------------------------------------------------------"
deactivate
set +x
ARTIFACT=./$ENVIRONEMNT_NAME"_testlogs.tar.gz"

# Check if the *.tar.gz exists before attempting to remove it
if [ -f "$ARTIFACT" ]; then
    rm "$ARTIFACT"
    echo "$ARTIFACT removed successfully."
fi

# Create acrtifact
tar -cvzf "$ENVIRONEMNT_NAME"_testlogs.tar.gz "$LOG_DIR" >/dev/null 2>&1
if [ -f "$ARTIFACT" ]; then
    echo "Artifact $ARTIFACT created successfully."
fi

# show contents of artifact
tar -tzvf "$ENVIRONEMNT_NAME"_testlogs.tar.gz

# Cleanup
rm -rf "$ENVIRONEMNT_NAME"
echo "Done"
