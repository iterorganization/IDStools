#####################
 IDStools Cheatsheet
#####################

This cheat sheet provides quick reference of commonly used commands in IDStools.


****************
 Analysis Tools
****************

+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Command                    | Description and Example Usage                                                                                                |
+============================+==============================================================================================================================+
| *plotcoresources*          | Plots core_sources results (replaces csplot).                                                                                |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotcoresources --uri "imas:mdsplus?user=public;pulse=130012;run=105;database=TEST;version=3"                           |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotcoretransport*        | Core plasma transport of particles, energy,                                                                                  |
|                            | momentum and poloidal flux (replaces check_transport).                                                                       |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotcoretransport --uri "imas:mdsplus?user=public;pulse=92436;run=850;database=TEST;version=3"                          |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|*ploteccomposition*         | Display ec results (replaces eccomp).                                                                                        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ ploteccomposition --uri "imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3"                        |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|*plotecray*                 | Display EC wave ray-tracing results (replaces ecray).                                                                        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotecray --uri "imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3"  -md wall                      |
|                            |                                                                                                                              |
|                            |    $ plotecray --uri "imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3"                                |
|                            |    -md "imas:hdf5?user=public;pulse=116000;run=4;database=ITER_MD;version=3#wall"                                            |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|*plotecstrayradiation*      | Shows electron cyclotron stray radiation.                                                                                    |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotecstrayradiation --uri "imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3"                     |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotedgeprofiles*         | Shows edge profiles plots by interpolating on rectangular                                                                    |
|                            | grid.                                                                                                                        |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotedgeprofiles --uri "imas:mdsplus?user=public;pulse=123314;run=1;database=ITER;version=3" --wall                     |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotequilibrium*          | Shows plasma equilibrium  (replaces equiplot).                                                                               |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotequilibrium --uri "imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3"                          |
|                            |    -md "imas:mdsplus?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active"                                  |
|                            |    "imas:hdf5?user=public;pulse=116000;run=4;database=ITER_MD;version=3#wall" --phi                                          |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotequicomp*             | Shows plasma equilibrium and quantities related with it                                                                      |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotequicomp --uri "imas:hdf5?user=public;shot=105027;run=200;database=ITER;version=3"                                  |
|                            |    "imas:hdf5?user=public;shot=105027;run=2;database=ITER;version=3"                                                         |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *printfluxes*              | Shows flux information from available                                                                                        |
|                            | transport models  (replaces print_fluxes).                                                                                   |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ printfluxes --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" -m CLOSEST                    |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plothcddistributions*     | shows waveforms  (replaces hcd_distributions_plot).                                                                          |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plothcddistributions --uri "imas:mdsplus?user=public;pulse=130012;run=115;database=TEST;version=3"                      |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plothcd*                  | shows plots from distributions and waves for                                                                                 |
|                            | different data entries for analysis   (replaces hcd_plot).                                                                   |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plothcd       -ech 134173/101/public/MDSPLUS/TEST/3                                                                     |
|                            |    -nbi 130012/115/public/MDSPLUS/TEST/3                                                                                     |
|                            |    -fus 130012/115/public/MDSPLUS/TEST/3                                                                                     |
|                            |    -icrh 130012/15/public/MDSPLUS/TEST/3                                                                                     |
|                            |                                                                                                                              |
|                            |    $ plothcd -ech "imas:mdsplus?user=public;pulse=134173;run=101;database=TEST;version=3"                                    |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plothcdwaves*             | shows waveforms  (replaces hcd_waves_plot).                                                                                  |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plothcdwaves --uri "imas:mdsplus?user=public;pulse=134173;run=101;database=TEST;version=3"                              |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotkineticprofiles*      | Shows plasma kinetic profiles from the core                                                                                  |
|                            | profiles  (replaces kinplot).                                                                                                |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotkineticprofiles --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"                       |
|                            |                                                                                                                              |
|                            |    $ plotkineticprofiles --uri "imas:mdsplus?path=/work/imas/shared/imasdb/ITER/3/134174/117" # access layer 5 and above     |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotmachinedescription*   | Plots machine description data stored in databases.                                                                          |
|                            | (replaces mdplot)                                                                                                            |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotmachinedescription --uri "imas:hdf5?user=public;pulse=116000;run=4;database=ITER_MD;version=3"                      |
|                            |                                                                                                                              |
|                            |    $ plotmachinedescription --uri "imas:mdsplus?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active"       | 
|                            |                                                                                                                              |              
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotneutron*              | Plots particles vs normalised toroidal                                                                                       |
|                            | flux coordinate  (replaces neutronplot).                                                                                     |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotneutron --uri "imas:mdsplus?user=public;pulse=121014run=11;database=ITER;version=3" -t 450                          |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *printplasmacompo*         | Display the plasma composition from the                                                                                      |
|                            | core_profiles IDS  (replaces ids_compo).                                                                                     |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ printplasmacompo --uri "imas:mdsplus?user=public;pulse=131047;run=4;database=ITER;version=3"                            |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotpressure*             | Display the plasma kinetic profiles from .                                                                                   |
|                            | the core_profiles  (replaces pressureplot).                                                                                  |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotpressure --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"                              |
|                            |                                                                                                                              |
|                            |    $ plotpressure --uri "imas:mdsplus?path=/work/imas/shared/imasdb/ITER/3/134174/117" access layer 5 and above              |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotrotation*             | Plasma kinetic profiles from the core_profiles                                                                               |
|                            | (replaces rotationplot)                                                                                                      |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotrotation --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"                              |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotscenario*             | Display the plasma kinetic profiles and equilibrium from                                                                     | 
|                            | the core_profiles and equilibrium  (replaces scenplot).                                                                      | 
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotscenario --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" --time 60                    |
|                            |                                                                                                                              |
|                            |    $ plotscenario --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" --no-profiles                |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *printcoresources*         | Shows source information from available                                                                                      |
|                            |  sources (replaces print_sources).                                                                                           |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ printcoresources --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"                          |
|                            |                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
| *plotspectrometry*         | Displays the spectrum, displaying plots of radiance                                                                          |
|                            | and intensity in two different windows (replaces svplot).                                                                    |   
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+
|                            |                                                                                                                              |
|                            | .. code-block:: bash                                                                                                         |
|                            |                                                                                                                              |
|                            |    $ plotspectrometry --uri "imas:mdsplus?user=public;pulse=134000;run=37;database=TEST;version=3"                           |
|                            |                                                                                                                              |
|                            |    $ plotspectrometry --uri "imas:mdsplus?path=/work/imas/shared/imasdb/TEST/3/134000/37" access layer 5 and above           |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------+



************************
 IDS Manipulation Tools
************************

+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| Command                       | Description and Example Usage                                                                                                       |
+===============================+=====================================================================================================================================+
| *eqdsk2ids*                   | EQDSK Convertor.                                                                                                                    | 
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ eqdsk2ids -c 11                                                                                                                |
|                               |    -g resources/geqdsk/example.gfile --dest "imas:mdsplus?user=$USER;pulse=134174;run=117;database=ITER;version=3"                  | 
|                               |    --log INFO                                                                                                                       |
|                               |                                                                                                                                     | 
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idscp*                       | Copy ids from one pulse to another                                                                                                  |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idscp --src "imas:mdsplus?user=public;pulse=131024;run=10;database=ITER;version=3"                                             |
|                               |    --dest "imas:mdsplus?user=$USER;pulse=145000;run=5;database=ITER;version=3"                                                      |
|                               |                                                                                                                                     | 
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idsdiff*                     | Shows ids level differences between two runs. It stores result in                                                                   |
|                               | html document. For signals differences it is also shown as graph.                                                                   |  
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3#summary"                                    |
|                               |    "imas:mdsplus?user=public;pulse=122525;run=2;database=ITER;version=3#summary"                                                    |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=130011;run=6;database=ITER;version=3#summary"                                    |
|                               |    "imas:mdsplus?user=public;pulse=130012;run=4;database=ITER;version=3#summary"                                                    |
|                               |                                                                                                                                     | 
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=122481;run=1;database=ITER;version=3                                             |
|                               |    #edge_profiles/ggd[:]/electrons/density[1].values"                                                                               |
|                               |    "imas:mdsplus?user=public;pulse=122481;run=2;database=ITER;version=3#edge_profiles/ggd[:]/electrons/density[1].values"           |
|                               |    --plot                                                                                                                           |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3                                           |
|                               |    #core_profiles/profiles_1d(:)/electrons/temperature[10]"                                                                         |
|                               |    "imas:mdsplus?user=public;pulse=134174;run=107;database=ITER;version=3#core_profiles/profiles_1d(:)/electrons/temperature[0]"    |
|                               |    --plot                                                                                                                           |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3                                           |
|                               |    #core_profiles/profiles_1d(40:60)/electrons/temperature"                                                                         |
|                               |    "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d(40:60)/electrons/temperature"   |
|                               |    --plot                                                                                                                           |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=131024;run=50;database=ITER;version=3"                                           |
|                               |    "imas:mdsplus?user=sawantp1;pulse=131024;run=50;database=ITER;version=3"                                                         |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=130011;run=6;database=ITER;version=3#summary"                                    |
|                               |    "imas:mdsplus?user=public;pulse=130012;run=4;database=ITER;version=3#summary"                                                    |
|                               |                                                                                                                                     |
|                               |    $ idsdiff --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3#summary"                                    |
|                               |    "imas:mdsplus?user=public;pulse=122525;run=2;database=ITER;version=3#summary"                                                    |
|                               |                                                                                                                                     |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idslist*                     | Shows list of all idses along with count of time slices.                                                                            |
|                               | (replaces ids_content(yaml), listidss (with time slices),                                                                           |    
|                               | idsoccurrences(occ) merged into one script)                                                                                         |                                            
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |  
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idslist --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3"                                            |
|                               |                                                                                                                                     | 
|                               |    $ idslist --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" -y  # output in yaml format                |
|                               |                                                                                                                                     | 
|                               |    $ idslist --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" -c  # occurrence with comment              |  
|                               |                                                                                                                                     |
|                               |    $ idslist --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" -f  # Shows full time array                |    
|                               |                                                                                                                                     |                                                       
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idsperf*                     | Shows performance of access layer operations on dataset. timing and                                                                 |
|                               | performance information for different types of operations on IDS                                                                    |
|                               | data with the IMAS Python Access Layer.                                                                                             |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"                                          |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" equilibrium                              |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=134174;run=117;daabase=ITER;version=3" equilibrium --show-stats --repeat 2       |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" equilibrium  -a                          |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" equilibrium  -t 50 -m                    |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" summary                                    |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" summary --verbose --output-run 5           |
|                               |    --show-stats --repeat 2                                                                                                          |
|                               |                                                                                                                                     | 
|                               |    $ idsperf --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" summary --verbose --output-run 5           |
|                               |    --show-stats --repeat 2                                                                                                          |
|                               |                                                                                                                                     | 
|                               |    --uri-out "imas:mdsplus?user=$USER;pulse=131024;run=25;database=ITER;version=3" --memory-backend                                 |
|                               |                                                                                                                                     | 
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idsprint*                    | Dumps or prints all data on the console.                                                                                            |
|                               | Check if specific fields or attributes have been filled out or empty                                                                |
|                               | The output can also be saved to a file using extraction                                                                             |
|                               | (Replaces idsdump, idsdumppath)                                                                                                     |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3#equilibrium"                               |
|                               |                                                                                                                                     | 
|                               |    # print child node information and metadata                                                                                      | 
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d" -i            |
|                               |                                                                                                                                     | 
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]"            |
|                               |                                                                                                                                     | 
|                               |    # compact output print only names which has data                                                                                 | 
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]" -c         |
|                               |                                                                                                                                     | 
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]" -f         |
|                               |                                                                                                                                     | 
|                               |    # Show empty fields of ids alone with filled ids fields                                                                          |
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]/e_field" -e |
|                               |                                                                                                                                     | 
|                               |    # plot 1d array                                                                                                                  |
|                               |    $ idsprint --uri "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/105027/2#magnetics/flux_loop[:]/flux/data" -p                   |
|                               |                                                                                                                                     | 
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=122481;run=1;database=ITER;version=3#edge_profiles/ggd[:]/electrons/density[1]  |
|                               |    .values" -p                                                                                                                      |
|                               |                                                                                                                                     | 
|                               |    $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3                                          |
|                               |    #core_profiles/profiles_1d(:)/electrons/temperature" -p                                                                          |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idsresample*                 | Resample IDSs from a data-entry and save them into another                                                                          |
|                               | data-entry based on PREVIOUS_INTERP method.                                                                                         |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idsresample --src "imas:mdsplus?user=public;pulse=131024;run=10;database=ITER;version=3"                                       |
|                               |    --dest "imas:mdsplus?user=$USER;pulse=131024;run=5;database=ITER;version=3"  --index-range 0,,10                                 | 
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idsrescale_equilibrium*      | Rescaling an equilibrium magnetic field, storing the output into                                                                    |
|                               | another entry of the same DB. replaced by ids_rescale_eq                                                                            |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idsrescale_equilibrium --src "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3"                             |
|                               |    --dest "imas:mdsplus?user=$USER;pulse=122222;run=22;database=ITER;version=3"  --rescale 2                                        |    
|                               |                                                                                                                                     |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idsshift_equilibrium*        | Rigidly shifts vertically an equilibrium, storing the output into                                                                   |
|                               | another entry of the same DB. replaced by ids_shift_eq                                                                              |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idsshift_equilibrium --src "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3"                               |
|                               |    --dest "imas:mdsplus?user=$USER;pulse=123001;run=1;database=ITER;version=3"  --shift -0.01                                       |   
|                               |                                                                                                                                     |                                                       
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
| *idssize*                     | IDS size in bytes and the time taken to read each object. It also                                                                   |
|                               | shows total size of all IDS objects in the data entry. It shows                                                                     |
|                               | total time taken to read all objects from the data entry. It is                                                                     |
|                               | helpful for performance check of IDS objects.                                                                                       |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+
|                               |                                                                                                                                     |
|                               | .. code-block:: bash                                                                                                                |
|                               |                                                                                                                                     |
|                               |    $ idssize --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3" equilibrium                                |
|                               |                                                                                                                                     | 
|                               |    $ idssize --uri "imas:mdsplus?user=public;pulse=131024;run=10;database=ITER;version=3"                                           |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------+



****************                                                                           
Database Tools
**************** 

+---------------------+---------------------------------------------------------------------+
| Command             | Description and Example Usage                                       |
+=====================+=====================================================================+
| *dbconverter*       | Copy all data-entries from one database into another one            |
+---------------------+---------------------------------------------------------------------+
|                     |                                                                     |
|                     | .. code-block:: bash                                                |
|                     |                                                                     |
|                     |   $ dbconverter --user $USER --database ITER -do MYDB -bo HDF5      |
|                     |                                                                     |
+---------------------+---------------------------------------------------------------------+
| *dblist*            | Lists existing IMAS databases (Replaces imasdbs).                   |
+---------------------+---------------------------------------------------------------------+
|                     |                                                                     |
|                     | .. code-block:: bash                                                |
|                     |                                                                     |
|                     |    $ dblist -u public -d TEST list                                  |
|                     |                                                                     |
|                     |    $ dblist -u public -d TEST list -c                               |
|                     |                                                                     |
|                     |    $ dblist -u public -d TEST list -M                               |
|                     |                                                                     |
|                     |    $ dblist databases                                               |
|                     |                                                                     |
|                     |    $ dblist dataversions                                            |
+---------------------+---------------------------------------------------------------------+
| *dbperf*            | Check performance of database                                       |
+---------------------+---------------------------------------------------------------------+
|                     |                                                                     |
|                     | .. code-block:: bash                                                |
|                     |                                                                     |
|                     |   $ dbperf -d TEST                                                  |
|                     |                                                                     |
+---------------------+---------------------------------------------------------------------+
| *dbscraper*         | The `dbscraper` script scrapes data from a particular               |
|                     | IDS path for a specified series of pulses and displays the pulse    |
|                     | along with the value.  (Replaces db_extractor)                      |
+---------------------+---------------------------------------------------------------------+
|                     |                                                                     |
|                     | .. code-block:: bash                                                |
|                     |                                                                     |
|                     |    $ dbscraper "equilibrium/time_slice*0*/global_quantities/volume" |
|                     |    --list-count 2                                                   |
|                     |                                                                     |
|                     |    $ dbscraper "core_profiles/profiles_1d(0)/electrons/temperature" |
|                     |    --list-count 2                                                   |
|                     |                                                                     |
+---------------------+---------------------------------------------------------------------+
| *dbselector*        | The `dbselector` script shows lists of all scenarios where          |
|                     | specified ids exists. Just provide idsname as input argument to the |
|                     | script.                                                             |
+---------------------+---------------------------------------------------------------------+
|                     |                                                                     |
|                     | .. code-block:: bash                                                |
|                     |                                                                     |
|                     |    $ dbselector -d TEST core_profiles --list-count 2                |
|                     |    $ dbselector -d TEST summary --list-count 2                      |
|                     |                                                                     |
+---------------------+---------------------------------------------------------------------+

**************************
 Scenario Database Tools
**************************

.. warning::
   Scenario Database tools are keeping their legacy arguments as they will be soon deprecated and replaced by SimDB.

+--------------------------------+--------------------------------------------------------------------------------+
| Command                        | Description and Example Usage                                                  |
+================================+================================================================================+
| *create_db_entry*              | Auto-generated yaml scenario and watcher files                                 |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ create_db_entry -s 130012 -r 105 -d TEST --disable-validation             |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *create_db_entry_disruption*   | Auto-generated yaml scenario and watcher files for disruption                  |
|                                | database                                                                       |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ create_db_entry_disruption -s 100028 -r 1 -d ITER_DISRUPTIONS             |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *disruption_summary*           | Script to list available disruptions in a specific folder                      |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ disruption_summary                                                        |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *md_status*                    | Show status and potential parent and children for a given                      |
|                                | simulation stored in ITER machine description database folder                  |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ md_status -s 116000 -r 3                                                  |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *md_summary*                   | md_summary list available machine description data in a specific               |
|                                | folder with search facility                                                    |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ md_summary  -s 150502/102                                                 |
|                                |                                                                                |
|                                |    $ md_summary  -s nbi on-on                                                  |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *scenario_status*              | The `scenario_status` program provides information about the                   |
|                                | scenario of specified shot and run number from the scenario                    |
|                                | database. It shows status and potential parent and children for a              |
|                                | given simulation stored in ITER scenario description database                  |
|                                | folder                                                                         |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ scenario_status -s 134174 -r 117                                          |
|                                |                                                                                |
|                                |    $ scenario_status -s 130012 -r 4 --print                                    |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *scenario_summary*             | The `scenario_summary` lists available scenarios in a specific                 |
|                                | folder with search facility.                                                   |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ scenario_summary -s He4,2.65                                              |
|                                |                                                                                |
|                                |    $ scenario_summary -s He4,2.65 -c shot,run,database,composition             |
|                                |                                                                                |
|                                |    $ scenario_summary -s He4 2.65                                              |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *show_db_entry*                | Show full description file for a given simulation stored in ITER DB            |
|                                | folder.                                                                        |
|                                |                                                                                |
|                                | .. code-block:: bash                                                           |
|                                |                                                                                |
|                                |    $ show_db_entry -s 134174 -r 117                                            |
|                                |                                                                                |
+--------------------------------+--------------------------------------------------------------------------------+
| *watch_db_entry*               | Subscribe/unsubscribe as a watcher to a simulation file                        |
|                                | stored in IMAS DB                                                              |
+--------------------------------+--------------------------------------------------------------------------------+

