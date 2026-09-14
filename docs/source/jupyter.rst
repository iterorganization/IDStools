#######################
 Jupyter notebook usage
#######################

IDStools command-line tools can also be used directly from Jupyter notebooks.
Import ``idstools`` once in the notebook kernel to register the IDStools
commands as IPython line magics:

.. code-block:: python

   import idstools

After that, commands such as ``idsprint`` and ``plotequilibrium`` can be
called with ``%``:

.. code-block:: python

   %idsprint -u "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117#core_profiles/profiles_1d[0]/electrons/temperature" -p

.. code-block:: python

   %plotequilibrium -u "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/100507/5"


******************************
 Interactive Matplotlib plots
******************************

For interactive Matplotlib figures in Jupyter, use the ``ipympl`` backend. If
``ipympl`` is installed in the same Python environment as IDStools, the backend
can be selected with Matplotlib's notebook magic before plotting:

.. code-block:: python

   %matplotlib widget
   import idstools

   %idsprint -u "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117#core_profiles/profiles_1d[0]/electrons/temperature" -p

Alternatively, the backend can be selected through the IDStools ``--rc``
option before Matplotlib has been imported in the current kernel:

.. code-block:: python

   import idstools

   %idsprint -u "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/134174/117#core_profiles/profiles_1d[0]/electrons/temperature" -p --rc "backend='module://ipympl.backend_nbagg'"

.. code-block:: python

   %plotequilibrium -u "imas:hdf5?path=/work/imas/shared/imasdb/ITER/3/100507/5" --rc "backend='module://ipympl.backend_nbagg'"
