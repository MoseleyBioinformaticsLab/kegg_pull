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
Functionality for getting KEGG entries from the KEGG REST API, parsing them, and saving the entries as files. A JSON file, called ``pull-results.json``, is saved describing the results of the pull. Below is the interpretation of each of the fields:

**percent-success:** The percentage of the requested entries that were successfully pulled and saved in a file.

**pull-minutes:** The number of minutes that the pull took to complete.

**num-successful:** The number of entries that were successfully pulled and saved in a file.

**num-failed:** The number of entries that failed to be pulled.

**num-timed-out:** The number of entries that timed out when requested.

**num-total:** The number of total entry IDs requested.

**successful-entry-ids:** The list of successful entry IDs.

**failed-entry-ids:** The list of failed entry IDs.

**timed-out-entry-ids:** The list of timed out entry IDs.

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
