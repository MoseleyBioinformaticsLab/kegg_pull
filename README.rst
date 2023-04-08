#########
kegg_pull
#########
Description
-----------
The ``kegg_pull`` package provides a number of useful CLI and API features for interacting with the KEGG REST API. This includes wrapper methods/commands for all the REST API operations, pulling lists of KEGG entry IDs, and pulling an arbitrary number of KEGG entries, in a single call, that are automatically separated and saved in individual files.

Documentation
-------------
The complete documentation for our API and CLI including tutorials can be found `here <https://moseleybioinformaticslab.github.io/kegg_pull/>`__.

Installation
------------
Requires python 3.10 and above.

Install on Linux, Mac OS X
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. parsed-literal::
   python3 -m pip install kegg-pull

Install on Windows
~~~~~~~~~~~~~~~~~~
.. parsed-literal::
   py -3 -m pip install kegg-pull

**Note:** Many KEGG entry IDs contain colons and ``kegg_pull`` saves KEGG entry files with their ID in the file name. When running on Windows, all file names with colons will have their colons replaced with underscores.

**Note:** If ``py`` is not installed on Windows (e.g. Python was installed via the Windows store rather than from the official Python website), the installation command is the same as Linux and Mac OS X.

**Note:** If the ``kegg_pull`` console script is not found on Windows, the CLI can be used via ``python3 -m kegg_pull`` or ``py -3 -m kegg_pull`` or ``path\to\console\script\kegg_pull.exe``. Alternatively, the directory where the console script is located can be added to the Path environment variable. For example, the console script may be installed at:

.. parsed-literal::
   c:\\users\\<username>\\appdata\\local\\programs\\python\\python310\\Scripts\\

PyPi
~~~~
See our PyPi page `here <https://pypi.org/project/kegg-pull/>`__.

Questions, Feature Requests, and Bug Reports
--------------------------------------------
Please submit any questions or feature requests you may have and report any potential bugs/errors you observe on `our GitHub issues page <https://github.com/MoseleyBioinformaticsLab/kegg_pull/issues>`__.

Dependencies
------------
Note, the ``pip`` command will install dependencies automatically.

.. parsed-literal::
   docopt
   requests
   tqdm
   jsonschema

Get the source code
-------------------
Code is available on GitHub: https://github.com/MoseleyBioinformaticsLab/kegg_pull.

You can clone the repository via:

.. parsed-literal::
   git clone https://github.com/MoseleyBioinformaticsLab/kegg_pull.git

Once you have a copy of the source, you can embed it in your own Python package, or install it into your system site-packages easily:

Linux, Mac OS X
~~~~~~~~~~~~~~~
.. parsed-literal::
   python3 setup.py install

Windows
~~~~~~~
.. parsed-literal::
   py -3 setup.py install
