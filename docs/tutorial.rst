Tutorial
========

API
---

.. code:: ipython3

    import kegg_pull as kp

CLI
---

.. code:: ipython3

    ! kegg_pull --full-help


.. parsed-literal::

    
    Usage:
        kegg_pull -h | --help       Show this help message.
        kegg_pull --full-help       Show the help message of all sub commands.
        kegg_pull entry-ids ...     Obtain a list of KEGG entry IDs.
        kegg_pull rest ...          Executes one of the KEGG REST API operations.
        kegg_pull pull ...          Pull, separate, and store KEGG entries to the local file system.
    
    --------------------------------------------------------------------------------
    
    Usage:
        kegg_pull entry-ids -h | --help
        kegg_pull entry-ids from-database <database-name> [--output=<output>]
        kegg_pull entry-ids from-file <file-path> [--output=<output>]
        kegg_pull entry-ids from-keywords <database-name> <keywords> [--output=<output>]
        kegg_pull entry-ids from-molecular-attribute <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>]
    
    Options:
        -h --help                               Show this help message.
        from-database                           Gets all the entry IDs within a given database.
        <database-name>                         The KEGG database from which to get a list of entry IDs.
        --output=<output>                       Path to the file to store the output (1 entry ID per line). Prints to the console if not specified.
        from-file                               Loads the entry IDs from a file.
        <file-path>                             Path to a file containing a list of entry IDs with one entry ID on each line.
        from-keywords                           Searches for entries within a database based on provided keywords.
        <keywords>                              Comma separated list of keywords to search within entries (e.g. --keywords=kw1,k2w,kw3 etc.).
        from-molecular-attribute                Searches a database of molecule-type KEGG entries by molecular attributes.
        --formula=<formula>                     Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searchers for molecule entries containing 5 oxygen atoms and/or 7 carbon atoms).
        --exact-mass=<exact-mass>               Either a single number (e.g. --exact-mass=155.5) or two numbers (e.g. --exact-mass=155.5 --exact-mass=244.4). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
        --molecular-weight=<molecular-weight>   Same as --exact-mass but searches based on the molecular weight.
    
    --------------------------------------------------------------------------------
    
    Usage:
        kegg_pull rest -h | --help
        kegg_pull rest info <database-name> [--output=<output>]
        kegg_pull rest list <database-name> [--output=<output>]
        kegg_pull rest get <entry-ids> [--entry-field=<entry-field>] [--output=<output>]
        kegg_pull rest find <database-name> <keywords> [--output=<output>]
        kegg_pull rest find <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>]
        kegg_pull rest conv <kegg-database-name> <outside-database-name> [--output=<output>]
        kegg_pull rest conv --conv-target=<target-database-name> <entry-ids> [--output=<output>]
        kegg_pull rest link <target-database-name> <source-database-name> [--output=<output>]
        kegg_pull rest link --link-target=<target-database-name> <entry-ids> [--output=<output>]
        kegg_pull rest ddi <drug-entry-ids> [--output=<output>]
    
    Options:
        -h --help                               Show this help message.
        info                                    Executes the "info" KEGG API operation, getting information about a KEGG database.
        <database-name>                         The name of the database to get information about or entry IDs from.
        list                                    Executes the "list" KEGG API operation, getting the entry IDs of the provided database.
        --output=<output>                       The file to store the response body from the KEGG web API operation. Prints to the console if --output is not specified.
        get                                     Executes the "get" KEGG API operation, getting the entries of the provided entry IDs.
        <entry-ids>                             Comma separated list of entry IDs.
        --entry-field=<entry-field>             Optional field to extract from an entry instead of the default entry info (i.e. flat file or htext in the case of brite entries).
        find                                    Executes the "find" KEGG API operation, finding entry IDs based on provided queries.
        <keywords>                              Comma separated list of keywords to search entries with.
        --formula=<formula>                     Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searchers for molecule entries containing 5 oxygen atoms and/or 7 carbon atoms).
        --exact-mass=<exact-mass>               Either a single number (e.g. --exact-mass=155.5) or two numbers (e.g. --exact-mass=155.5 --exact-mass=244.4). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
        --molecular-weight=<molecular-weight>   Same as --exact-mass but searches based on the molecular weight.
        conv                                    Executes the "conv" KEGG API operation, converting entry IDs from an outside database to those of a KEGG database and vice versa.
        <kegg-database-name>                    The name of the KEGG database from which to view equivalent outside database entry IDs.
        <outside-database-name>                 The name of the non-KEGG database from which to view equivalent KEGG database entry IDs.
        --conv-target=<target-database-name>    The outside or KEGG database from which to view equivalent versions of the provided entry IDs. If a KEGG database, the provided entry IDs must be from an outside database and vice versa.
        link                                    Executes the "link" KEGG API operation, showing the IDs of entries that are connected/related to entries of other databases.
        <target-database-name>                  The name of the database to find cross-references in the source database.
        <source-database-name>                  The name of the database from which cross-references are found in the target database.
        --link-target-<target-database-name>    The name of the database to find cross-references in the provided entry IDs.
        ddi                                     Executes the "ddi" KEGG API operation, searching for drug to drug interactions. Providing one entry ID reports all known interactions, while providing multiple checks if any drug pair in a given set of drugs is CI or P. If providing multiple, all entries must belong to the same database.
        <drug-entry-ids>                        Comma separated list of drug entry IDs from the following databases: drug, ndc, or yj
    
    --------------------------------------------------------------------------------
    
    Usage:
        kegg_pull pull -h | --help
        kegg_pull pull multiple (--database-name=<database-name>|--file-path=<file-path>) [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output=<output>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]
        kegg_pull pull single (--entry-ids=<entry-ids>|--file-path=<file-path>) [--output=<output>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]
    
    Options:
        -h --help                           Show this help message.
        multiple                            Pull, separate, and store as many entries as requested via multiple automated requests to the KEGG web API. Useful when the number of entries requested is well above the maximum that KEGG allows for a single request.
        --database-name=<database-name>     The KEGG database from which to get a list of entry IDs to pull.
        --file-path=<file-path>             Path to a file containing a list of entry IDs to pull, with one entry ID on each line.
        --force-single-entry                Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if --database-name is "brite".
        --multi-process                     If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
        --n-workers=<n-workers>             The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
        --output=<output>                   The directory where the pulled KEGG entries will be stored. Defaults to the current working directory. If ends in .zip, entries are saved to a zip archive instead of a directory.
        --entry-field=<entry-field>         Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
        --n-tries=<n-tries>                 The number of times to attempt a KEGG request before marking it as timed out or failed. Defaults to 3.
        --time-out=<time-out>               The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 60.
        --sleep-time=<sleep-time>           The amount of time to wait after a KEGG request times out before attempting it again. Defaults to 0.
        single                              Pull, separate, and store one or more KEGG entries via a single request to the KEGG web API. Useful when the number of entries requested is less than or equal to the maximum that KEGG allows for a single request.
        --entry-ids=<entry-ids>             Comma separated list of entry IDs to pull in a single request (e.g. --entry-ids=id1,id2,id3 etc.).
    

