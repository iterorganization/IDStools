#########
 idsdiff
#########

*idsdiff* script shows ids level differences between two runs. It stores
result in html document. For signals differences it is also shown as
graph.

****************
 Syntax idsdiff
****************

   .. command-output:: idsdiff -h

*****************
 Example idsdiff
*****************


   .. code-block:: bash

      # Compare with specific idses using --ids option
      $ idsdiff --uri "imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3#summary" "imas:mdsplus?user=public;pulse=122525;run=2;database=ITER;version=3#summary"
                                    First: imas:mdsplus?user=public;pulse=122525;run=1;database=ITER;version=3 (summary) -                              
                                    Second: imas:mdsplus?user=public;pulse=122525;run=2;database=ITER;version=3 (summary)                               
      ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
      ┃ IDS Path                                ┃ Description       ┃ Value first                            ┃ Value second                            ┃
      ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
      │ ids_properties/comment                  │ different values  │ (STR_0D) b2mn     B2.5 bjb99/7         │ (STR_0D) b2mn     B2.5 bjb99/7          │
      │                                         │                   │ SOLPS-ITER  2021-10-14  17:31 bonninx  │ SOLPS-ITER  2023-02-23  20:05 bonninx   │
      │                                         │                   │ ITER#2525_(F57-120-N_1.2%-Be0,_tau=0.… │ ITER#2525_(F57-120-N_1.2%-Be0,_tau=0.2… │
      │ ids_properties/source                   │ missing in second │ (STR_0D) SOLPS4.3                      │                                         │
      │ ids_properties/creation_date            │ different values  │ (STR_0D) 20211014 173342.600  +0200    │ (STR_0D) 20230223 200711.139  +0100     │
      │ ids_properties/version_put/data_dictio… │ different values  │ (STR_0D) 3.33.0                        │ (STR_0D) 3.38.0                         │
      │ ids_properties/version_put/access_layer │ different values  │ (STR_0D) 4.9.2                         │ (STR_0D) 4.11.1                         │
      │ tag/name                                │ different values  │ (STR_0D) 3.0.7                         │ (STR_0D) 3.0.8                          │
      │ configuration/source                    │ missing in first  │                                        │ (STR_0D) SOLPS4.3                       │
      │ global_quantities/r0/source             │ different values  │ (STR_0D) SOLPS4.3                      │ (STR_0D) ITER Baseline q95=3            │
      │                                         │                   │                                        │ equilibrium                             │

   .. code-block:: bash

      # Use ids name in the URI using # (hash) parameter
      $ idsdiff --uri "imas:mdsplus?user=public;pulse=130011;run=6;database=ITER;version=3#summary" "imas:mdsplus?user=public;pulse=130012;run=4;database=ITER;version=3#summary"

   .. code-block:: bash

      # compare all available IDSes
      $ idsdiff --uri "imas:mdsplus?user=public;pulse=131024;run=50;database=ITER;version=3"  "imas:mdsplus?user=sawantp1;pulse=131024;run=50;database=ITER;version=3"
                     First: imas:mdsplus?user=public;pulse=131024;run=50;database=ITER;version=3 (equilibrium) -                 
                     Second: imas:mdsplus?user=sawantp1;pulse=131024;run=50;database=ITER;version=3 (equilibrium)                
      ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
      ┃ IDS Path                                         ┃ Description      ┃ Value first     ┃ Value second                     ┃
      ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
      │ ids_properties/version_put/data_dictionary       │ different values │ (STR_0D) 3.38.1 │ (STR_0D) 3.42.0                  │
      │ ids_properties/version_put/access_layer          │ different values │ (STR_0D) 4.11.2 │ (STR_0D) 5.3.2                   │
      │ ids_properties/version_put/access_layer_language │ different values │ (STR_0D) python │ (STR_0D) python-5.3.1+5-ge7f9725 │
      └──────────────────────────────────────────────────┴──────────────────┴─────────────────┴──────────────────────────────────┘
               IDS availability            
      ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
      ┃ IDS                  ┃ Availability ┃
      ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
      │ core_sources         │ second       │
      │ distribution_sources │ second       │
      │ wall                 │ second       │
      │ core_profiles        │ second       │
      │ nbi                  │ second       │
      │ summary              │ second       │
      │ pf_active            │ second       │
      └──────────────────────┴──────────────┘

   .. code-block:: bash

      # compare plot by providing field path
      $ idsdiff --uri "imas:mdsplus?user=public;pulse=122481;run=1;database=ITER;version=3#edge_profiles/ggd[:]/electrons/density[1].values" "imas:mdsplus?user=public;pulse=122481;run=2;database=ITER;version=3#edge_profiles/ggd[:]/electrons/density[1].values" --plot

      $ idsdiff --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d(:)/electrons/temperature[10]" "imas:mdsplus?user=public;pulse=134174;run=107;database=ITER;version=3#core_profiles/profiles_1d(:)/electrons/temperature[0]" --plot

      $ idsdiff --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d(40:60)/electrons/temperature" "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d(40:60)/electrons/temperature" --plot

   .. image:: _static/images/idsdiff_1.png
      :alt: image not found
      :align: center

   .. image:: _static/images/idsdiff_2.png
      :alt: image not found
      :align: center

   .. image:: _static/images/idsdiff_3.png
      :alt: image not found
      :align: center

   .. image:: _static/images/idsdiff_4.png
      :alt: image not found
      :align: center

   .. image:: _static/images/idsdiff_5.png
      :alt: image not found
      :align: center
