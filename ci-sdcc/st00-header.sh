#!/bin/bash
source /etc/profile.d/modules.sh

module use /work/imas/etc/modules/all
shopt -s expand_aliases
module purge

# Check which modules env var is set
if [ -n "${INTEL_MODULES:-}" ]; then
    MODULES_LIST="$INTEL_MODULES"
    export ENVIRONEMNT_NAME="intel"
elif [ -n "${FOSS_MODULES:-}" ]; then
    MODULES_LIST="$FOSS_MODULES"
    export ENVIRONEMNT_NAME="foss"
else
    echo ""
    echo "ERROR: Neither INTEL_MODULES nor FOSS_MODULES is set"
    echo ""
    echo "Please set one of these environment variables and run the script."
    echo ""
    echo "Examples:"
    echo ""
    echo "  For intel-2023b:"
    echo "    export INTEL_MODULES=\"IMAS-Core/5.7.1-intel-2023b Tkinter/3.11.5-GCCcore-13.2.0 IMAS-Python/2.3.0-intel-2023b PyYAML/6.0.1-GCCcore-13.2.0\""
    echo ""
    echo "  For intel-2025b:"
    echo "    export INTEL_MODULES=\"IMAS-Core/5.7.1-intel-2025b Tkinter/3.13.5-GCCcore-14.3.0 IMAS-Python/2.3.0-intel-2025b PyYAML/6.0.2-GCCcore-14.3.0\""
    echo ""
    echo "  For foss-2023b:"
    echo "    export FOSS_MODULES=\"IMAS-Core/5.7.1-foss-2023b Tkinter/3.11.5-GCCcore-13.2.0 IMAS-Python/2.3.0-foss-2023b PyYAML/6.0.1-GCCcore-13.2.0\""
    echo ""
    echo "  For foss-2025b:"
    echo "    export FOSS_MODULES=\"IMAS-Core/5.7.1-foss-2025b Tkinter/3.13.5-GCCcore-14.3.0 IMAS-Python/2.3.0-foss-2025b PyYAML/6.0.2-GCCcore-14.3.0\""
    echo ""
    exit 1
fi

# Load all modules
for module in $MODULES_LIST; do
    module load "$module"
done
