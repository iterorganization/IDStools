##############
 Installation
##############

*IDStools* is a Python package, so the Python environment is
mandatory. Its functioning depends on IMASPy and the data dictionary. As a
result, before running *IDStools* scripts, the IMAS environment must be
loaded.

***********
 For users
***********

Install using pip 

.. code-block:: bash

   $ git clone ssh://git@git.iter.org/imas/idstools.git
   $ pip install --upgrade pip
   $ pip install --upgrade wheel setuptools
   $ pip install .

Also it is possible to install it in the Python virtual environment

.. code-block:: bash

   $ git clone ssh://git@git.iter.org/imas/idstools.git
   $ cd idstools
   $ python -m venv idsenv
   $ source idsenv/bin/activate
   $ pip install --upgrade pip
   $ pip install .
   $ deactivate

   $ idslist -h

.. note::

   If you are using ITER sdcc cluster then IDStools is available by
   doing module load as shown below

.. code-block:: bash

   $ module load IDStools/*

.. note::

   There are development versions of IDStools on SDCC. These can be used if 
   you need functionalities/bug fixes before next release 

.. code-block:: bash

   $ module av -i -t idstools/dev
   /work/imas/etc/modules/all:
   IDStools/dev-* 


****************
 For Developers
****************

.. note ::
   IDStools is currently hosted in ITER repository server 
   Get access to https://git.iter.org/projects/IMAS/repos/idstools  repository if you don't it have already

Clone *IDStools* repository.

.. code-block:: bash

   $ git clone ssh://git@git.iter.org/imas/idstools.git

If you wish to include additional tools or expand functionalities,
submit pull requests.

The *IDStools* test suite should be run as follows.:
To run pytest

.. code-block:: bash

   $ cd idstools
   $ export PYTHONPATH=$PWD:$PYTHONPATH
   $ pytest

To run tests scripts and verify functionalities

you may need additional Linux commands if it is not installed e.g. bc

.. code-block:: bash

   sudo yum install bc

.. code-block:: bash

   $ cd idstools
   $ tests/st01_test_ids_scripts_with_uri.sh
   $ tests/st02_test_db_scripts.sh
   $ tests/st03_test_analysis_scripts_with_uripath.sh
   $ tests/st03_test_analysis_scripts_with_uri.sh
   $ tests/st04_test_scenario_scripts.sh

To build the *IDStools* documentation, execute:

.. code-block:: bash

   $ pip install .[docs]
   $ make -C docs realclean
   $ make -C docs autogen
   $ make -C docs html
   $ make -C docs man

Code formatting is done with the black

.. code-block:: bash

   black -l 120 idstools
   
Append commits related to the formatting of the code `.git-blame-ignore-revs` file which is 
placed in the root of the repository

Configure git to ignore formatting related commits

.. code-block:: bash

   $ git config blame.ignoreRevsFile .git-blame-ignore-revs

pre-commit hooks are used in the repository, It just need to be configured
Ensure pre-commit is aready installled 

.. code-block:: bash

   $ pip install pre-commit
   $ pre-commit install
   pre-commit installed at .git/hooks/pre-commit

More information: 
https://black.readthedocs.io/en/stable/integrations/source_version_control.html
https://pre-commit.com/#install
