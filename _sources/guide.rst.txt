Guide
=====
Description
-----------
The ``kegg_pull`` package provides a number of useful CLI and API features for interacting with the KEGG REST API. This includes wrapper methods/commands for all the REST API operations, getting lists of KEGG entry IDs, and getting an unlimited number of KEGG entries, in a single call, that are automatically separated and saved in individual files.

Installation
------------
Requires python 3.8 and above.

Install on Linux, Mac OS X
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. parsed-literal::

   python3 -m pip install kegg_pull

Install on Windows
~~~~~~~~~~~~~~~~~~
.. parsed-literal::
   py -3 -m pip install

Dependencies
------------
Note, the ``pip`` command will install dependencies automatically.

.. literalinclude:: ../requirements.txt

Get the source code
-------------------
Code is available on GitHub: https://github.com/MoseleyBioinformaticsLab/KEGGpull.

You can clone the repository via:

.. parsed-literal::
   git clone https://github.com/MoseleyBioinformaticsLab/KEGGpull.git

Once you have a copy of the source, you can embed it in your own Python package, or install it into your system site-packages easily:

.. parsed-literal::
   python3 setup.py install

