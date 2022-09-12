CLI
===

KEGG pull Commandline Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Top-level commandline interface.

.. literalinclude:: ../src/kegg_pull/__main__.py
    :start-at: Usage:
    :end-before: """
    :language: none

Pulling, Parsing, and Saving KEGG Entries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for getting KEGG entries from the KEGG REST API, parsing them, and saving the entries as files.

.. literalinclude:: ../src/kegg_pull/pull_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none

Getting Lists of KEGG Entry IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for getting lists of KEGG entry IDs from the KEGG REST API.

.. literalinclude:: ../src/kegg_pull/entry_ids_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none

KEGG REST API Operations
~~~~~~~~~~~~~~~~~~~~~~~~
Interface for the KEGG REST API including all its operations.

.. literalinclude:: ../src/kegg_pull/rest_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none
