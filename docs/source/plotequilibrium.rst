#################
 plotequilibrium
#################

*plotequilibrium* script shows plasma equilibrium. Optionally it also
shows PF coil positions and a toroidal-flux contour overlay.
`refer data dictionary <https://imas-data-dictionary.readthedocs.io/en/latest/>`_.

``--phi`` overlays contours of the toroidal magnetic flux Φ(R,Z) [Wb] read directly from
``equilibrium/time_slice/profiles_2d/phi``:

.. math::

   \Phi(R,Z) \quad [\mathrm{Wb}]

.. versionchanged:: 2.5.0

   Removed the ``--show-labels`` option. Remove it from existing commands.


************************
 Syntax plotequilibrium
************************

   .. command-output:: plotequilibrium -h


*************************
 Example plotequilibrium
*************************

   .. code-block:: bash

        $ plotequilibrium --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" --phi -md pf_active wall --profiles
        $ plotequilibrium --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3" --phi -md "imas:mdsplus?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active" "imas:mdsplus?user=public;pulse=116000;run=4;database=ITER_MD;version=3#wall"
        $ plotequilibrium --uri "imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3" --phi --md "imas:mdsplus?user=public;pulse=111001;run=103;database=ITER_MD;version=3#pf_active" "imas:hdf5?user=public;pulse=116000;run=4;database=ITER_MD;version=3#wall"
        $ plotequilibrium --uri "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/100507/5" --md "imas:hdf5?path=/work/imas/shared/imasdb/ITER_MD/3/116000/5#wall" --profiles --no-provenance

   .. image:: _static/images/plotequilibrium.png
      :alt: image not found
      :align: center

   .. image:: _static/images/plotequilibrium2.png
      :alt: image not found
      :align: center

   .. image:: _static/images/plotequilibrium3.png
      :alt: image not found
      :align: center
