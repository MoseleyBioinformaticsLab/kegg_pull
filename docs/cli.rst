.. |Functionality| replace:: Provides commandline functionality
.. |Interface for| replace:: Provides commandline functionality for accessing

CLI
===
**Note:** Many KEGG entry IDs contain colons and ``kegg_pull`` saves KEGG entry files with their ID in the file name. When running on Windows, all file names with colons will have their colons replaced with underscores.

kegg_pull Commandline Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Top-level commandline interface.

.. literalinclude:: ../src/kegg_pull/__main__.py
    :start-at: Usage:
    :end-before: """
    :language: none

.. include:: ../src/kegg_pull/pull.py
    :start-after: """
    :end-before: """

A JSON file, called ``pull-results.json``, is saved, describing the results of the pull. Below is the interpretation of each of the fields:

**percent-success:** The percentage of the requested entries that were successfully pulled and saved in a file.

**pull-minutes:** The number of minutes that the pull took to complete.

**num-successful:** The number of entries that were successfully pulled and saved in a file.

**num-failed:** The number of entries that failed to be pulled.

**num-timed-out:** The number of entries that timed out when requested.

**num-total:** The number of total entry IDs requested.

**successful-entry-ids:** The list of successful entry IDs.

**failed-entry-ids:** The list of failed entry IDs.

**timed-out-entry-ids:** The list of timed out entry IDs.

If the ``--unsuccessful-threshold`` option is set and surpassed, an ``aborted-pull-results.json`` file is instead output with the following fields:

**num-remaining-entry-ids:** The number of requested entries remaining after the process aborted. The process aborted before ``kegg_pull`` could even try to pull these entries.

**num-successful:** The number of entries that were successfully pulled before the process aborted.

**num-failed:** The number of entries that failed by the time the process aborted.

**num-timed-out:** The number of entries that timed out by the time the process aborted.

**remaining-entry-ids:** The IDs of the remaining entries.

**successful-entry-ids:** The IDs of the successful entries.

**failed-entry-ids:** The IDs of the failed entries.

**timed-out-entry-ids:** The IDs of the timed out entries.

.. literalinclude:: ../src/kegg_pull/pull_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none

.. include:: ../src/kegg_pull/entry_ids.py
    :start-after: """
    :end-before: """

.. literalinclude:: ../src/kegg_pull/entry_ids_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none

.. include:: ../src/kegg_pull/map.py
    :start-after: """
    :end-before: """

.. literalinclude:: ../src/kegg_pull/map_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none

.. include:: ../src/kegg_pull/rest.py
    :start-after: """
    :end-before: """

.. literalinclude:: ../src/kegg_pull/rest_cli.py
    :start-at: Usage:
    :end-before: """
    :language: none
