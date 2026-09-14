#!/bin/bash
# Bamboo test execution script for analysis scripts
# Execute script from root directory
source ./tests/st00_common.sh
# expand aliases
shopt -s expand_aliases

#print hostname
hostname -f

# create log directory
if [ -z "$1" ]; then
    LOG_DIR=$PWD/"logs"
    mkdir -p "$LOG_DIR"
else
    LOG_DIR="$1"
fi

if [ -z "$2" ]; then
    DATABASE_DIR=$PWD/"db"
    mkdir -p "$DATABASE_DIR"
else
    DATABASE_DIR="$2"
fi

# "viewall database --uri \"imas:hdf5?user=schneim;pulse=92436;run=271;database=jet;version=3\""
# 

SCRIPTS=(
    "plotcoresources --uri \"imas:mdsplus?user=public;pulse=130012;run=105;database=TEST;version=3\" --save --directory $LOG_DIR"
    "plotcoretransport --uri \"imas:mdsplus?user=public;pulse=92436;run=850;database=TEST;version=3\" --save --directory $LOG_DIR"
    "ploteccomposition --uri \"imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3\" --save --directory $LOG_DIR"
    "plotecray --uri \"imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3\" --save --directory $LOG_DIR"
    "plotecray --uri \"imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3\" -md wall --save --directory $LOG_DIR"
    "plotedgeprofiles --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --wall --time 60 --save --directory $LOG_DIR"
    "plotequilibrium --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --phi -md \"imas:hdf5?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active\" \"imas:hdf5?user=public;pulse=116000;run=5;database=ITER_MD;version=3#wall\" --save --directory $LOG_DIR"
    "plotequilibrium --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" -md pf_active wall --save --directory $LOG_DIR"
    "printfluxes --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" -m CLOSEST"
    "plothcd -ech 134173/101/public/MDSPLUS/TEST/3 -nbi 130012/115/public/MDSPLUS/TEST/3 -fus 130012/115/public/MDSPLUS/TEST/3 -icrh 130012/115/public/MDSPLUS/TEST/3 --save --directory $LOG_DIR"
    "plothcddistributions --uri \"imas:mdsplus?user=public;pulse=130012;run=115;database=TEST;version=3\" --save --directory $LOG_DIR"
    "plothcdwaves --uri \"imas:mdsplus?user=public;pulse=134173;run=101;database=TEST;version=3\" --save --directory $LOG_DIR"
    "plotkineticprofiles --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --save --directory $LOG_DIR"
    "plotmachinedescription --uri \"imas:hdf5?user=public;pulse=116000;run=5;database=ITER_MD;version=3\" --save --directory $LOG_DIR"
    "plotmachinedescription --uri \"imas:hdf5?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active\" --save --directory $LOG_DIR"
    "plotneutron --uri \"imas:hdf5?user=public;pulse=121014;run=11;database=ITER;version=3\" -t 450 --save --directory $LOG_DIR"
    "printplasmacompo --uri \"imas:hdf5?user=public;pulse=131047;run=27;database=ITER;version=3\""
    "plotpressure --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --save --directory $LOG_DIR"
    "plotrotation --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --save --directory $LOG_DIR"
    "plotscenario --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --time 60 --save --directory $LOG_DIR"
    "plotscenario --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --no-profiles --save --directory $LOG_DIR"
    "printcoresources --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\""
    "plotspectrometry --uri \"imas:mdsplus?user=public;pulse=134000;run=37;database=TEST;version=3\" --save --directory $LOG_DIR"
    "plotkineticprofiles --uri \"imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117\" --save --directory $LOG_DIR"
    "plotpressure --uri \"imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117\" --save --directory $LOG_DIR"
    "plotspectrometry --uri \"imas:mdsplus?path=/work/imas/shared/imasdb/TEST/3/134000/37\" --save --directory $LOG_DIR")

execute_scripts "${SCRIPTS[@]}"
return $?


# "plotcoresources --uri \"imas:hdf5?user=public;pulse=130012;run=105;database=TEST;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotcoretransport --uri \"imas:hdf5?user=public;pulse=92436;run=850;database=TEST;version=3\" --dd-update --save --directory $LOG_DIR"
# "ploteccomposition --uri \"imas:hdf5?user=public;pulse=134173;run=2326;database=TEST;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotecray --uri \"imas:hdf5?user=public;pulse=134173;run=2326;database=TEST;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotecray --uri \"imas:hdf5?user=public;pulse=134173;run=2326;database=TEST;version=3\" -md wall --dd-update --save --directory $LOG_DIR"
# "plotedgeprofiles --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --wall --time 60 --dd-update --save --directory $LOG_DIR"
# "plotequilibrium --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --phi -md \"imas:hdf5?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active\" \"imas:hdf5?user=public;pulse=116000;run=5;database=ITER_MD;version=3#wall\" --dd-update --save --directory $LOG_DIR"
# "plotequilibrium --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" -md pf_active wall --dd-update --dd-update --save --directory $LOG_DIR"
# "printfluxes --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" -m CLOSEST --dd-update"
# "plothcd -ech 134173/101/public/MDSPLUS/TEST/3 -nbi 130012/115/public/MDSPLUS/TEST/3 -fus 130012/115/public/MDSPLUS/TEST/3 -icrh 130012/115/public/MDSPLUS/TEST/3 --dd-update --save --directory $LOG_DIR"
# "plothcddistributions --uri \"imas:hdf5?user=public;pulse=130012;run=115;database=TEST;version=3\" --dd-update --save --directory $LOG_DIR"
# "plothcdwaves --uri \"imas:hdf5?user=public;pulse=134173;run=101;database=TEST;version=3\" --save --dd-update --directory $LOG_DIR"
# "plotkineticprofiles --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotmachinedescription --uri \"imas:hdf5?user=public;pulse=116000;run=5;database=ITER_MD;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotmachinedescription --uri \"imas:hdf5?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active\" --dd-update --save --directory $LOG_DIR"
# "plotneutron --uri \"imas:hdf5?user=public;pulse=121014;run=11;database=ITER;version=3\" -t 450 --dd-update --save --directory $LOG_DIR"
# "printplasmacompo --uri \"imas:hdf5?user=public;pulse=131047;run=4;database=ITER;version=3\""
# "plotpressure --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotrotation --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotscenario --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --time 60 --dd-update --save --directory $LOG_DIR"
# "plotscenario --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\" --no-profiles --dd-update --save --directory $LOG_DIR"
# "printcoresources --uri \"imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3\""
# "plotspectrometry --uri \"imas:hdf5?user=public;pulse=134000;run=37;database=TEST;version=3\" --dd-update --save --directory $LOG_DIR"
# "plotkineticprofiles --uri \"imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117\" --dd-update --save --directory $LOG_DIR"
# "plotpressure --uri \"imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117\" --dd-update --save --directory $LOG_DIR"
# "plotspectrometry --uri \"imas:hdf5?path=/work/imas/shared/imasdb/TEST/3/134000/37\" --dd-update --save --directory $LOG_DIR"