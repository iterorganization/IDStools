#!/bin/bash
source /etc/profile.d/modules.sh
source ./ci-sdcc/utils.sh
##########################################################################################
#                     Set environment based on toolchain                                 #
##########################################################################################

module use /work/imas/etc/modules/all

# expand aliases
shopt -s expand_aliases

#print hostname
hostname -f

IMAS_EXISTS=$(module -r -t list 2>&1 | grep -E "IMAS-Core"  | head -n 1) 
if [ -n "$IMAS_EXISTS" ]; then
    echo "> Found already loaded IMAS Module : $IMAS_EXISTS"
    ACCESS_LAYER_VERSION=$(echo "$AL_VERSION" | cut -d '.' -f 1)
    TOOLCHAIN_VERSION=$(echo "$IMAS_EXISTS" | awk -F '-' '{print $(NF-1)"-"$NF}')
else
    echo "> IMAS Module is not loaded"
fi

if [ -n "$1" ] || [ -n "$2" ]; then
    echo "> Compiling with $1 and Access Layer $2 with latest version of installed modules.Previously loaded modules will be purged.."
    module purge
    # If toolchain version is passed then purge all modules
    if [ -n "$1" ]; then
        TOOLCHAIN_VERSION="$1"
    fi

    # Get AL version
    if [ -n "$2" ]; then
        ACCESS_LAYER_VERSION="$2"
    else
        ACCESS_LAYER_VERSION="5"
    fi
fi

if [ -z "$TOOLCHAIN_VERSION" ]; then
    echo "> No toolchain found, Setting it to default : intel-2023b"
    TOOLCHAIN_VERSION="intel-2023b"
fi

if [ -z "$ACCESS_LAYER_VERSION" ]; then
    ACCESS_LAYER_VERSION="5"
fi

if [ -z "$DD_VERSION" ]; then 
    DD_VERSION="3"
else
    DD_VERSION="$3"
fi

echo "> Building for $TOOLCHAIN_VERSION and Access Layer $ACCESS_LAYER_VERSION"

if [[ $TOOLCHAIN_VERSION == *"intel"* ]]; then
    FCOMPILER="ifort"
fi
if [[ $TOOLCHAIN_VERSION == *"foss"* ]]; then
    FCOMPILER="gfortran"
fi


CORE_MODULE_VERSION=$(getIMASCoreModuleName "$TOOLCHAIN_VERSION" "$ACCESS_LAYER_VERSION" "$DD_VERSION")
# load IMAS module first

if [ -z "$IMAS_EXISTS" ]; then
    echo "> IMAS is not loaded.. Loading Module $CORE_MODULE_VERSION"
    module load "$CORE_MODULE_VERSION"
fi

GCCcore_VERSION=$(getGCCcoreVersion)
module purge

dependencies="./ci-sdcc/dependencies.txt"

# Check if the file exists
if [ ! -f "$dependencies" ]; then
    echo "File $dependencies not found."
    return 1
fi

declare -a RUNMODULES=()
declare -a EBBRUNMODULES=()

echo "-------------------------------------------------------"
echo "> dependency modules"
counter=0
while IFS= read -r line || [[ -n $line ]]; do
    line="${line// /}"
    # for empty string continue
    if [[ -z "$line" ]]; then
        counter=$(("$counter" + 1))
        continue
    fi
    # fix module version
    if [[ $line == *"/"* ]]; then
        echo "using fix module $line"
        RUNMODULES["$counter"]="$line"
        EBBRUNMODULES["$counter"]="('$line', EXTERNAL_MODULE),"
        counter=$(("$counter" + 1))
        continue
    fi
    # latest module version as it is not given
    # if [[ $line == *"IMAS"* ]]; then
    #     echo "    IMAS $CORE_MODULE_VERSION"
    #     RUNMODULES["$counter"]="$CORE_MODULE_VERSION"
    #     EBBRUNMODULES["$counter"]="('$CORE_MODULE_VERSION', EXTERNAL_MODULE),"
    # else
    module_version=$(getModuleName "$line" "$TOOLCHAIN_VERSION" "$GCCcore_VERSION")
    echo "    $line $module_version"
    RUNMODULES["$counter"]="$module_version"
    EBBRUNMODULES["$counter"]=$(getModuleNameAndVersion "$module_version")

    # fi
    counter=$(("$counter" + 1))
done <"$dependencies"
echo "-------------------------------------------------------"

echo "> Details of environment"
echo "    TOOLCHAIN_VERSION : $TOOLCHAIN_VERSION"
echo "    GCCcore_VERSION : $GCCcore_VERSION"
echo "    IMAS VERSION : $CORE_MODULE_VERSION"
echo "    RUNMODULES : " "${RUNMODULES[@]}"
echo "    EBRUNMODULES : " "${EBBRUNMODULES[@]}"
echo "    Compiler : $FCOMPILER"
echo "-------------------------------------------------------"


echo "> Loading run time modules"
# Load build modules if they exist
for imodule in "${RUNMODULES[@]}"; do
    IFS='/' read -r iname iversion <<< "$imodule"
    MODULE_EXISTS=$(module -r -t list 2>&1 | grep -E "$iname/")
    if [ -z "$MODULE_EXISTS" ]; then
        echo "    $iname not available, Loading $imodule"
        module load "$imodule"
    else
        echo "    $MODULE_EXISTS already loaded"
    fi
done
echo "> Done"
echo "-------------------------------------------------------"
