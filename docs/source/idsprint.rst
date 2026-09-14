##########
 idsprint
##########

*idsprint* command prints the content of an IDSes to the terminal. Users can specify a URI 
to define the data entry path. The command supports various options, allowing users to view empty fields, 
print all array elements, focus on fields with data, inspect metadata, or plot 1D arrays from the IDS fields. 
It can also save generated figures to a specified directory or the default location.


*****************
 Syntax idsprint
*****************

   .. command-output:: idsprint -h


******************
 Example idsprint
******************

   .. code-block:: bash

      # it is possible to inspect ids field using idsprint
      $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d" -i
      ╭───── IDS array of structures: profiles_1d (DD version 3.42.0) ──────╮
      │ Core plasma radial profiles for various time slices                 │
      │ ╭─────────────────────────────────────────────────────────────────╮ │
      │ │ value = [                                                       │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[0])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[1])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[2])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[3])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[4])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[5])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[6])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[7])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[8])>, │ │
      │ │         │   <IDSStructure (IDS:core_profiles, profiles_1d[9])>, │ │
      │ │         │   ... +96                                             │ │
      │ │         ]                                                       │ │
      │ ╰─────────────────────────────────────────────────────────────────╯ │
      │ ╭────────────────────────── Attributes ───────────────────────────╮ │
      │ │ coordinates = <IDSCoordinates of 'profiles_1d'>                 │ │
      │ │                 0: 'profiles_1d(itime)/time'                    │ │
      │ │   has_value = True                                              │ │
      │ │    metadata = <IDSMetadata for 'profiles_1d'>                   │ │
      │ │       shape = (106,)                                            │ │
      │ │        size = 106                                               │ │
      │ ╰─────────────────────────────────────────────────────────────────╯ │
      ╰─────────────────────────────────────────────────────────────────────╯


   .. code-block:: bash

      # view complete tree of ids field using idsprint and check which data is filled
      $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]" 
      profiles_1d
      ├── profiles_1d[0]/grid
      │   ├── rho_tor_norm: array([-0.0017,  0.0017,  0.005 , ...,  0.9933,  0.9966,  1.    ])
      │   ├── rho_tor: array([-0.0043,  0.0043,  0.013 , ...,  2.5667,  2.5753,  2.584 ])
      │   ├── psi: array([ 1.7381e+01,  1.7381e+01,  1.7381e+01, ...,  1.1796e-01,  5.8720e-02, -2.7637e-08])
      │   ├── volume: array([-4.6259e-03,  4.6259e-03,  2.3129e-02, ...,  7.3460e+02,  7.3898e+02,  7.4335e+02])
      │   └── area: array([5.9593e-05, 5.9593e-05, 5.3633e-04, ..., 1.9476e+01, 1.9603e+01, 1.9730e+01])
      ├── profiles_1d[0]/electrons
      │   ├── temperature: array([1490.9207, 1490.9207, 1489.9044, ...,   49.4664,   45.7809,   41.9821])
      │   ├── density: array([5.3978e+18, 5.3978e+18, 5.3984e+18, ..., 2.3647e+18, 2.2721e+18, 2.1800e+18])
      │   ├── density_thermal: array([5.3978e+18, 5.3978e+18, 5.3984e+18, ..., 2.3647e+18, 2.2721e+18, 2.1800e+18])
      │   ├── pressure_thermal: array([1289.3981, 1289.3981, 1288.6679, ...,   18.7413,   16.6655,   14.6638])
      │   └── collisionality_norm: array([1105.0601, 1105.0601,  123.0365, ...,   32.9046,   36.9473,   40.9901])
      ├── profiles_1d[0]/ion[0]
      │   ├── profiles_1d[0]/ion[0]/element[0]
      │   │   ├── a: 2.0
      │   │   ├── z_n: 1.0
      │   │   └── atoms_n: 1
      │   ├── z_ion: 1.0
      │   ├── label: 'D'
      │   ├── name: 'D'
      │   ├── neutral_index: 1
      │   ├── z_ion_1d: array([1., 1., 1., ..., 1., 1., 1.])
      │   ├── z_ion_square_1d: array([1., 1., 1., ..., 1., 1., 1.])
      │   ├── temperature: array([891.8207, 891.8207, 891.4358, ...,  72.0662,  70.2118,  68.3453])
      │   ├── density: array([2.5504e+18, 2.5504e+18, 2.5507e+18, ..., 1.1550e+18, 1.1094e+18, 1.0640e+18])
      │   ├── density_thermal: array([2.5504e+18, 2.5504e+18, 2.5507e+18, ..., 1.1550e+18, 1.1094e+18, 1.0640e+18])
      │   ├── pressure_thermal: array([364.4206, 364.4206, 364.3042, ...,  13.3359,  12.4804,  11.6511])
      │   ├── velocity_tor: array([ -0.    , -92.2832, -92.2583, ..., -74.3607, -74.7488, -75.1539])
      │   ├── velocity_pol: array([ 0.    ,  1.8106,  9.8227, ..., 58.2206, 57.0282, 57.0282])
      │   ├── profiles_1d[0]/ion[0]/velocity
      │   │   ├── poloidal: array([ 0.    ,  1.8106,  9.8227, ..., 58.2206, 57.0282, 57.0282])
      │   │   └── toroidal: array([ -0.    , -92.2832, -92.2583, ..., -74.3607, -74.7488, -75.1539])
      │   ├── multiple_states_flag: 1
      │   └── profiles_1d[0]/ion[0]/state[0]
      │       └── density_thermal: array([2.5504e+18, 2.5504e+18, 2.5507e+18, ..., 1.1550e+18, 1.1094e+18, 1.0640e+18])
      .
      ├── t_i_average: array([891.8207, 891.8207, 891.4358, ...,  72.0662,  70.2118,  68.3453])
      ├── n_i_thermal_total: array([5.1768e+18, 5.1768e+18, 5.1774e+18, ..., 2.3258e+18, 2.2342e+18, 2.1431e+18])
      ├── momentum_tor: array([-0.0000e+00, -1.2881e-05, -1.2879e-05, ..., -5.0121e-06, -4.8439e-06, -4.6759e-06])
      ├── momentum_phi: array([-0.0000e+00, -1.2881e-05, -1.2879e-05, ..., -5.0121e-06, -4.8439e-06, -4.6759e-06])
      ├── zeff: array([1.1637, 1.1637, 1.1637, ..., 1.061 , 1.0616, 1.0619])
      ├── pressure_ion_total: array([739.7033, 739.7048, 739.4746, ...,  26.8543,  25.1331,  23.4676])
      ├── pressure_thermal: array([2029.1014, 2029.1014, 2028.141 , ...,   45.5955,   41.7986,   38.1314])
      ├── j_total: array([-391858.8422, -391858.8422, -391057.4083, ...,  -15607.9471,  -13951.2367,  -12294.5263])
      ├── j_tor: array([-388437.6394, -388437.6394, -388149.7462, ...,  -13766.4592,  -12280.6587,  -11566.4002])
      ├── j_phi: array([-388437.6394, -388437.6394, -388149.7462, ...,  -13766.4592,  -12280.6587,  -11566.4002])
      ├── j_ohmic: array([-388432.3669, -388432.3669, -388124.089 , ...,  -13740.2629,  -12259.6731,  -11550.1127])
      ├── j_non_inductive: array([ -5.2725,  -5.2725, -25.6572, ..., -26.1963, -20.9856, -16.2875])
      ├── j_bootstrap: array([ -2.2622,  -2.2622, -21.0684, ..., -26.1959, -20.9853, -16.2872])
      ├── conductivity_parallel: array([56856983.6228, 56856983.6228, 56807225.7344, ...,   362621.2542,   323078.8177,   291312.3407])
      ├── profiles_1d[0]/e_field
      │   ├── radial: array([ -128.0971,  -128.0971,  -123.9098, ..., -1571.4791, -1565.848 , -1560.2169])
      │   └── parallel: array([-0.0069, -0.0069, -0.0069, ..., -0.0428, -0.0429, -0.043 ])
      ├── q: array([ 3.6316,  3.6316,  3.6317, ..., 12.4764, 12.6303, 12.7837])
      └── magnetic_shear: array([1.5337e-06, 1.5337e-06, 9.4825e-04, ..., 3.6307e+00, 3.6068e+00, 3.5829e+00])


   .. code-block:: bash

      # view complete tree without data using idsprint to get an overview
      $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]" -c
      14:17:09 INFO     Parsing data dictionary version 3.42.0 @dd_zip.py:166
      14:17:09 INFO     Parsing data dictionary version 3.31.0 @dd_zip.py:166
      profiles_1d
      ├── profiles_1d[0]/grid
      │   ├── rho_tor_norm
      │   ├── rho_tor
      │   ├── psi
      │   ├── volume
      │   └── area
      ├── profiles_1d[0]/electrons
      │   ├── temperature
      │   ├── density
      │   ├── density_thermal
      │   ├── pressure_thermal
      │   └── collisionality_norm
      ├── profiles_1d[0]/ion[0]
      │   ├── profiles_1d[0]/ion[0]/element[0]
      │   │   ├── a
      │   │   ├── z_n
      │   │   └── atoms_n
      │   ├── z_ion
      │   ├── label
      │   ├── name
      │   ├── neutral_index

   .. code-block:: bash

      # -f option of idsprint will allow to print full numpy arrays to check values in depth
      $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]" -f


   .. code-block:: bash

      # -e option of idsprint will show unfilled ids fields along wirh filled ones
      $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d[0]/e_field" -e
      14:24:58 INFO     Parsing data dictionary version 3.42.0 @dd_zip.py:166
      14:24:59 INFO     Parsing data dictionary version 3.31.0 @dd_zip.py:166
      e_field
      ├── radial: array([ -128.0971,  -128.0971,  -123.9098, ..., -1571.4791, -1565.848 , -1560.2169])
      ├── radial_error_upper  
      ├── radial_error_lower  
      ├── radial_error_index  
      ├── diamagnetic  
      ├── diamagnetic_error_upper  
      ├── diamagnetic_error_lower  
      ├── diamagnetic_error_index  
      ├── parallel: array([-0.0069, -0.0069, -0.0069, ..., -0.0428, -0.0429, -0.043 ])
      ├── parallel_error_upper  
      ├── parallel_error_lower  
      ├── parallel_error_index  
      ├── poloidal  
      ├── poloidal_error_upper  
      ├── poloidal_error_lower  
      ├── poloidal_error_index  
      ├── toroidal  
      ├── toroidal_error_upper  
      ├── toroidal_error_lower  
      └── toroidal_error_index 

   .. code-block:: bash
   
      # Plot ids field using idsprint
      $ idsprint --uri "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/105027/2#magnetics/flux_loop[:]/flux/data" -p

      $ idsprint --uri "imas:mdsplus?user=public;pulse=122481;run=1;database=ITER;version=3#edge_profiles/ggd[:]/electrons/density[1].values" -p

   $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#core_profiles/profiles_1d(:)/electrons/temperature" -p

   $ idsprint --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3#summary/time"

.. image:: _static/images/idsprint_1.png
   :alt: image not found
   :align: center

.. image:: _static/images/idsprint_2.png
   :alt: image not found
   :align: center

.. image:: _static/images/idsprint_3.png
   :alt: image not found
   :align: center
