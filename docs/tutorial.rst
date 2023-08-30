Tutorial
========

**Note:** Many KEGG entry IDs contain colons and ``kegg_pull`` saves
KEGG entry files with their ID in the file name. When running on
Windows, all file names with colons will have their colons replaced with
underscores.

API
---

``SinglePull``
~~~~~~~~~~~~~~

You can pull (request and save to the file system or save in memory) a
limited number of KEGG entries using the ``SinglePull`` class with the
list of entry IDs as input. The ``pull`` method stores the entries in
the file system and the ``pull_dict`` method stores them in memory,
specifically in a dictionary. The number of entries is limited because
only one request is made to the KEGG REST API and KEGG places a limit on
the number of entries that can be pulled with a single request. The
``output`` parameter in the ``pull`` method specifies where the entries
are saved based on whether ``output`` is a directory or ZIP archive if
it ends in “.zip”. The ``PullResult`` object that’s returned tells you
which of the entry IDs succeeded, which failed, and which timed out. In
this example, the entry ID succeeds.

``pull``
^^^^^^^^

.. code:: python3

    import kegg_pull.pull as p
    single_pull = p.SinglePull()
    entry_ids = ['br:br08902']
    pull_result = single_pull.pull(entry_ids=entry_ids, output='pull-entries/')
    print(pull_result)


.. parsed-literal::

    Successful Entry Ids: br:br08902
    Failed Entry Ids: none
    Timed Out Entry Ids: none


In this example, the entry ID fails.

.. code:: python3

    single_pull.pull(['br:br03220'], output='pull-entries/')




.. parsed-literal::

    Successful Entry Ids: none
    Failed Entry Ids: br:br03220
    Timed Out Entry Ids: none



When ``SinglePull`` pulls multiple entries at a time, they are
automatically separated from one another and saved in individual files.

.. code:: python3

    single_pull.pull(entry_ids=['cpd:C00001', 'cpd:C00002', 'cpd:C00003'], output='pull-entries/')




.. parsed-literal::

    Successful Entry Ids: cpd:C00001, cpd:C00002, cpd:C00003
    Failed Entry Ids: none
    Timed Out Entry Ids: none



An exception is thrown if you attempt to provide more entry IDs to the
``pull()`` method than what is accepted by KEGG.

.. code:: python3

    import logging as log
    
    try:
        single_pull.pull(entry_ids=['cpd:C00001', 'cpd:C00002', 'cpd:C00003', 'cpd:C00004', 'cpd:C00005', 'cpd:C00006',
            'cpd:C00007', 'cpd:C00008', 'cpd:C00009', 'cpd:C00010', 'cpd:C00011'], output='pull-entries/')
    except ValueError as error:
        log.error(error)


.. parsed-literal::

    ERROR:root:Cannot create URL - The maximum number of entry IDs is 10 but 11 were provided


``pull_dict``
^^^^^^^^^^^^^

The ``pull_dict`` method pulls entries just like the ``pull`` method
except that it stores the entries in memory rather than in the file
system. This is helpful if the user of the API wishes to use the entries
immediately and doesn’t need them to be stored persistently.
Specifically, ``pull_dict`` returns a tuple containing the
``PullResult`` as described above along with a dictionary mapping the
entry ID to the entry itself.

.. code:: python3

    pull_result, compounds = single_pull.pull_dict(
        entry_ids=['cpd:C00001', 'cpd:C00002', 'cpd:C00003'], entry_field='mol')

.. code:: python3

    pull_result




.. parsed-literal::

    Successful Entry Ids: cpd:C00001, cpd:C00002, cpd:C00003
    Failed Entry Ids: none
    Timed Out Entry Ids: none



The entries can be accessed from the dictionary using the provided entry
IDs as keys.

.. code:: python3

    print(compounds['cpd:C00001'])


.. parsed-literal::

     
     
     
      3  2  0  0  0  0  0  0  0  0999 V2000
       22.1250  -16.2017    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
       23.6000  -15.2112    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
       20.7129  -15.2859    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
      1  2  1  0     0  0
      1  3  1  0     0  0
    M  END
    
    > <ENTRY>
    cpd:C00001
    
    


``SingleProcessMultiplePull`` and ``MultiProcessMultiplePull``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get past the limit on the number of entries that can be pulled at a
time, we have two classes capable of pulling an arbitrary number of
entries. There’s the ``SingleProcessMultiplePull`` and
``MultiProcessMultiplePull``. ``MultiProcessMultiplePull`` will likely
pull faster since it pulls within multiple processes, but it requires
multiple cores. Like ``SinglePull``, these two classes have both a
``pull`` method and ``pull_dict`` method which respectively return a
``PullResult`` and a tuple containing a pull result and dictionary.

.. code:: python3

    multiple_pull = p.SingleProcessMultiplePull()
    
    entry_ids = [
        'cpd:C00001',
        'cpd:C00002',
        'cpd:C00003',
        'cpd:C00004',
        'cpd:C00005',
        'cpd:C00006',
        'cpd:C00007',
        'cpd:C00008',
        'cpd:C00009',
        'cpd:C00010',
        'cpd:C00011'
    ]
    
    multiple_pull.pull(entry_ids, output='pull-entries/')


.. parsed-literal::

    100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 11/11 [00:02<00:00,  3.72it/s]




.. parsed-literal::

    Successful Entry Ids: cpd:C00001, cpd:C00002, cpd:C00003, cpd:C00004, cpd:C00005, cpd:C00006, cpd:C00007, cpd:C00008, cpd:C00009, cpd:C00010, cpd:C00011
    Failed Entry Ids: none
    Timed Out Entry Ids: none



You can specify the number of processes to use for
``MultiProcessMultiplePull`` with the ``n_workers`` parameter, which
defaults to the number of cores available.

.. code:: python3

    multiple_pull = p.MultiProcessMultiplePull(n_workers=2)
    multiple_pull.pull(entry_ids, output='pull-entries/')


.. parsed-literal::

    100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 11/11 [00:01<00:00,  6.26it/s]




.. parsed-literal::

    Successful Entry Ids: cpd:C00001, cpd:C00002, cpd:C00003, cpd:C00004, cpd:C00005, cpd:C00006, cpd:C00007, cpd:C00008, cpd:C00009, cpd:C00010, cpd:C00011
    Failed Entry Ids: none
    Timed Out Entry Ids: none



The ``pull_dict`` method is also available:

.. code:: python3

    pull_result, compounds = multiple_pull.pull_dict(entry_ids, entry_field='mol')


.. parsed-literal::

    100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 11/11 [00:01<00:00, 10.72it/s]


.. code:: python3

    print(compounds['cpd:C00011'])


.. parsed-literal::

     
     
     
      3  2  0  0  0  0  0  0  0  0999 V2000
       21.8400  -11.9918    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
       20.6288  -12.6940    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
       23.0512  -12.6940    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
      1  2  2  0     0  0
      1  3  2  0     0  0
    M  END
    
    > <ENTRY>
    cpd:C00011
    
    $$$$
    


Entry IDs
~~~~~~~~~

The ``entry_ids`` module provides a number of different ways to pull a
list of KEGG entry IDs.

.. code:: python3

    import kegg_pull.entry_ids as ei
    entry_ids = ei.from_database('brite')
    print(entry_ids)


.. parsed-literal::

    ['br:br08901', 'br:br08902', 'br:br08904', 'br:br08906', 'br:ko00001', 'br:ko00002', 'br:ko00003', 'br:br08907', 'br:ko01000', 'br:ko01001', 'br:ko01009', 'br:ko01002', 'br:ko01003', 'br:ko01005', 'br:ko01011', 'br:ko01004', 'br:ko01008', 'br:ko01006', 'br:ko01007', 'br:ko00199', 'br:ko00194', 'br:ko03000', 'br:ko03021', 'br:ko03019', 'br:ko03041', 'br:ko03011', 'br:ko03009', 'br:ko03016', 'br:ko03012', 'br:ko03110', 'br:ko04131', 'br:ko04121', 'br:ko03051', 'br:ko03032', 'br:ko03036', 'br:ko03400', 'br:ko03029', 'br:ko02000', 'br:ko02044', 'br:ko02042', 'br:ko02022', 'br:ko02035', 'br:ko03037', 'br:ko04812', 'br:ko04147', 'br:ko02048', 'br:ko04030', 'br:ko04050', 'br:ko04054', 'br:ko03310', 'br:ko04040', 'br:ko04031', 'br:ko04052', 'br:ko04515', 'br:ko04090', 'br:ko01504', 'br:ko00535', 'br:ko00536', 'br:ko00537', 'br:ko04091', 'br:ko04990', 'br:ko03200', 'br:ko03210', 'br:ko03100', 'br:br08001', 'br:br08002', 'br:br08003', 'br:br08005', 'br:br08006', 'br:br08007', 'br:br08009', 'br:br08021', 'br:br08120', 'br:br08201', 'br:br08202', 'br:br08204', 'br:br08203', 'br:br08303', 'br:br08302', 'br:br08301', 'br:br08313', 'br:br08312', 'br:br08304', 'br:br08305', 'br:br08331', 'br:br08330', 'br:br08332', 'br:br08310', 'br:br08307', 'br:br08327', 'br:br08311', 'br:br08402', 'br:br08401', 'br:br08403', 'br:br08411', 'br:br08410', 'br:br08420', 'br:br08601', 'br:br08610', 'br:br08611', 'br:br08612', 'br:br08613', 'br:br08614', 'br:br08615', 'br:br08620', 'br:br08621', 'br:br08605', 'br:br03220', 'br:br03222', 'br:br03223', 'br:br01610', 'br:br01611', 'br:br01612', 'br:br01613', 'br:br01601', 'br:br01602', 'br:br01600', 'br:br01620', 'br:br01553', 'br:br01554', 'br:br01556', 'br:br01555', 'br:br01557', 'br:br01800', 'br:br01810', 'br:br08011', 'br:br08020', 'br:br08012', 'br:br08319', 'br:br08329', 'br:br08318', 'br:br08328', 'br:br08309', 'br:br08341', 'br:br08324', 'br:br08317', 'br:br08315', 'br:br08314', 'br:br08442', 'br:br08441', 'br:br08431']


Entry ID Mappings
~~~~~~~~~~~~~~~~~

The ``map`` module converts the output of the KEGG REST API “link”
operation or “conv” operation into dictionaries usable in python code.

“link” operation
^^^^^^^^^^^^^^^^

.. code:: python3

    import kegg_pull.map as kmap
    
    pathway_to_compound = kmap.entries_link(entry_ids=['path:map00010', 'path:map00020'], target_database='compound')
    print(pathway_to_compound)


.. parsed-literal::

    {'path:map00010': {'cpd:C00186', 'cpd:C00033', 'cpd:C00036', 'cpd:C00668', 'cpd:C06188', 'cpd:C01172', 'cpd:C05378', 'cpd:C00118', 'cpd:C06186', 'cpd:C00084', 'cpd:C05125', 'cpd:C00074', 'cpd:C00267', 'cpd:C00024', 'cpd:C00631', 'cpd:C00469', 'cpd:C00236', 'cpd:C00103', 'cpd:C00197', 'cpd:C00221', 'cpd:C00068', 'cpd:C15972', 'cpd:C00031', 'cpd:C00111', 'cpd:C01159', 'cpd:C16255', 'cpd:C15973', 'cpd:C05345', 'cpd:C00022', 'cpd:C06187', 'cpd:C01451'}, 'path:map00020': {'cpd:C00036', 'cpd:C00091', 'cpd:C00042', 'cpd:C00122', 'cpd:C05125', 'cpd:C00074', 'cpd:C00024', 'cpd:C00026', 'cpd:C16254', 'cpd:C00068', 'cpd:C15972', 'cpd:C00158', 'cpd:C00149', 'cpd:C00417', 'cpd:C16255', 'cpd:C15973', 'cpd:C05381', 'cpd:C00311', 'cpd:C05379', 'cpd:C00022'}}


“conv” operation
^^^^^^^^^^^^^^^^

.. code:: python3

    kegg_to_pubchem = kmap.entries_conv(entry_ids=['cpd:C00001', 'cpd:C00002'], target_database='pubchem')
    print(kegg_to_pubchem)


.. parsed-literal::

    {'cpd:C00001': {'pubchem:3303'}, 'cpd:C00002': {'pubchem:3304'}}


Pathway Organizer
~~~~~~~~~~~~~~~~~

The ``pathway_organizer`` module flattens a brite hierarchy into a
mapping of the IDs of its nodes to information about those nodes.

.. code:: python3

    import kegg_pull.pathway_organizer as po
    pathway_org = po.PathwayOrganizer.load_from_kegg()
    print(pathway_org.hierarchy_nodes['Metabolism'])


.. parsed-literal::

    {'name': 'Metabolism', 'level': 1, 'parent': None, 'children': ['Amino acid metabolism', 'Biosynthesis of other secondary metabolites', 'Carbohydrate metabolism', 'Chemical structure transformation maps', 'Energy metabolism', 'Global and overview maps', 'Glycan biosynthesis and metabolism', 'Lipid metabolism', 'Metabolism of cofactors and vitamins', 'Metabolism of other amino acids', 'Metabolism of terpenoids and polyketides', 'Nucleotide metabolism', 'Xenobiotics biodegradation and metabolism'], 'entry_id': None}


Rest API
~~~~~~~~

The ``KEGGrest`` class provides low-level wrapper methods for the KEGG
REST API, including all of its operations. The resulting
``KEGGresponse`` object contains both the text and binary versions of
the response body, the status of the response (one of ``SUCCESS``,
``FAILED``, or ``TIMEOUT``), and the internal URL used to request from
the KEGG REST API. For most use-cases, the higher-level ``kegg_pull``
functionality will be preferred over using the lower-level ``KEGGrest``
class. In fact, most of ``kegg_pull``\ ’s higher-level functionality
relies on the ``KEGGrest`` class, but provies a more useful programming
interface.

.. code:: python3

    import kegg_pull.rest as r
    kegg_rest = r.KEGGrest()
    kegg_response = kegg_rest.info(database='module')

.. code:: python3

    kegg_response.status




.. parsed-literal::

    <Status.SUCCESS: 1>



.. code:: python3

    kegg_response.text_body




.. parsed-literal::

    'module           KEGG Module Database\nmd               Release 106.0+/04-07, Apr 23\n                 Kanehisa Laboratories\n                 550 entries\n\nlinked db        pathway\n                 ko\n                 <org>\n                 genome\n                 compound\n                 glycan\n                 reaction\n                 enzyme\n                 disease\n                 pubmed\n'



.. code:: python3

    kegg_response.kegg_url




.. parsed-literal::

    https://rest.kegg.jp/info/module



CLI
---

The command line interface has 4 subcommands: ``pull``, ``entry-ids``,
``map``, and ``rest``. They are analogous to the API modules and
methods.

pull
~~~~

From a user-specified list of entry IDs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: none

    % kegg_pull pull entry-ids cpd:C00001,cpd:C00002,cpd:C00003 --output=compound-entries/


.. parsed-literal::

    100%|█████████████████████████████████████████████| 3/3 [00:01<00:00,  1.99it/s]


.. code:: none

    % head compound-entries/cpd:C00001.txt


.. parsed-literal::

    ENTRY       C00001                      Compound
    NAME        H2O;
                Water
    FORMULA     H2O
    EXACT_MASS  18.0106
    MOL_WEIGHT  18.0153
    REMARK      Same as: D00001
    REACTION    R00001 R00002 R00004 R00005 R00009 R00010 R00011 R00017 
                R00022 R00024 R00025 R00026 R00028 R00036 R00041 R00044 
                R00045 R00047 R00048 R00052 R00053 R00054 R00055 R00056 


The ``pull`` subcommand creates a ``pull-results.json``\ file. You can
load it as a dictionary using the python json library.

.. code:: python3

    import json as j
    
    with open('pull-results.json', 'r') as file:
        pull_results = j.load(file)
    
    print(pull_results)


.. parsed-literal::

    {'percent-success': 100.0, 'pull-minutes': 0.03, 'num-successful': 3, 'num-failed': 0, 'num-timed-out': 0, 'num-total': 3, 'successful-entry-ids': ['cpd:C00001', 'cpd:C00002', 'cpd:C00003'], 'failed-entry-ids': [], 'timed-out-entry-ids': []}


Below is what the ``pull-results.json`` file contents look like:

.. code:: none

    % cat pull-results.json


.. parsed-literal::

    {
    "percent-success": 100.0,
    "pull-minutes": 0.03,
    "num-successful": 3,
    "num-failed": 0,
    "num-timed-out": 0,
    "num-total": 3,
    "successful-entry-ids": [
    "cpd:C00001",
    "cpd:C00002",
    "cpd:C00003"
    ],
    "failed-entry-ids": [],
    "timed-out-entry-ids": []
    }

Entry IDs can also be passed in from standard input when the
``<entry-ids>`` option is equal to ``-`` rather than a comma-separated
list. This example saves the entries to a ZIP archive.

.. code:: python3

    standard_input = """
    cpd:C00001
    cpd:C00002
    cpd:C00003
    """
    
    with open('standard_input.txt', 'w') as file:
        file.write(standard_input)

.. code:: none

    % cat standard_input.txt | kegg_pull pull entry-ids - --output=compound-entries.zip


.. parsed-literal::

    100%|█████████████████████████████████████████████| 3/3 [00:01<00:00,  2.04it/s]


From a database
^^^^^^^^^^^^^^^

.. code:: none

    % kegg_pull pull database brite --multi-process --n-workers=11 --output=brite-entries/


.. parsed-literal::

    100%|█████████████████████████████████████████| 141/141 [00:19<00:00,  7.33it/s]


.. code:: none

    % ls brite-entries/


.. parsed-literal::

    br:br08001.txt	br:br08314.txt	br:br08610.txt	br:ko01003.txt	br:ko03036.txt
    br:br08002.txt	br:br08315.txt	br:br08611.txt	br:ko01004.txt	br:ko03037.txt
    br:br08003.txt	br:br08317.txt	br:br08612.txt	br:ko01005.txt	br:ko03041.txt
    br:br08005.txt	br:br08318.txt	br:br08613.txt	br:ko01006.txt	br:ko03051.txt
    br:br08006.txt	br:br08319.txt	br:br08614.txt	br:ko01007.txt	br:ko03100.txt
    br:br08007.txt	br:br08324.txt	br:br08615.txt	br:ko01008.txt	br:ko03110.txt
    br:br08009.txt	br:br08327.txt	br:br08620.txt	br:ko01009.txt	br:ko03200.txt
    br:br08021.txt	br:br08328.txt	br:br08621.txt	br:ko01011.txt	br:ko03210.txt
    br:br08120.txt	br:br08329.txt	br:br08901.txt	br:ko01504.txt	br:ko03310.txt
    br:br08201.txt	br:br08330.txt	br:br08902.txt	br:ko02000.txt	br:ko03400.txt
    br:br08202.txt	br:br08331.txt	br:br08904.txt	br:ko02022.txt	br:ko04030.txt
    br:br08203.txt	br:br08332.txt	br:br08906.txt	br:ko02035.txt	br:ko04031.txt
    br:br08204.txt	br:br08341.txt	br:br08907.txt	br:ko02042.txt	br:ko04040.txt
    br:br08301.txt	br:br08401.txt	br:ko00001.txt	br:ko02044.txt	br:ko04050.txt
    br:br08302.txt	br:br08402.txt	br:ko00002.txt	br:ko02048.txt	br:ko04052.txt
    br:br08303.txt	br:br08403.txt	br:ko00003.txt	br:ko03000.txt	br:ko04054.txt
    br:br08304.txt	br:br08410.txt	br:ko00194.txt	br:ko03009.txt	br:ko04090.txt
    br:br08305.txt	br:br08411.txt	br:ko00199.txt	br:ko03011.txt	br:ko04091.txt
    br:br08307.txt	br:br08420.txt	br:ko00535.txt	br:ko03012.txt	br:ko04121.txt
    br:br08309.txt	br:br08431.txt	br:ko00536.txt	br:ko03016.txt	br:ko04131.txt
    br:br08310.txt	br:br08441.txt	br:ko00537.txt	br:ko03019.txt	br:ko04147.txt
    br:br08311.txt	br:br08442.txt	br:ko01000.txt	br:ko03021.txt	br:ko04515.txt
    br:br08312.txt	br:br08601.txt	br:ko01001.txt	br:ko03029.txt	br:ko04812.txt
    br:br08313.txt	br:br08605.txt	br:ko01002.txt	br:ko03032.txt	br:ko04990.txt


.. code:: none

    % head pull-results.json


.. parsed-literal::

    {
    "percent-success": 85.11,
    "pull-minutes": 0.32,
    "num-successful": 120,
    "num-failed": 21,
    "num-timed-out": 0,
    "num-total": 141,
    "successful-entry-ids": [
    "br:br08901",
    "br:br08902",


Printing Entries
^^^^^^^^^^^^^^^^

Alternatively, you can print the KEGG entries to the screen rather than
saving them in separate files.

.. code:: none

    % kegg_pull pull entry-ids C00001,C00007 --entry-field=mol --print


.. parsed-literal::

    100%|█████████████████████████████████████████████| 2/2 [00:00<00:00,  2.56it/s]
    C00001
     
     
     
      3  2  0  0  0  0  0  0  0  0999 V2000
       22.1250  -16.2017    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
       23.6000  -15.2112    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
       20.7129  -15.2859    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
      1  2  1  0     0  0
      1  3  1  0     0  0
    M  END
    
    > <ENTRY>
    cpd:C00001
    
    
    
    C00007
    
     
     
     
      2  1  0  0  0  0  0  0  0  0999 V2000
       24.3446  -17.0048    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
       25.7446  -17.0048    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
      1  2  2  0     0  0
    M  END
    
    > <ENTRY>
    cpd:C00007
    
    
    


entry-ids
~~~~~~~~~

.. code:: none

    % kegg_pull entry-ids database brite --output=brite-entry-ids.txt
    % head brite-entry-ids.txt


.. parsed-literal::

    br:br08901
    br:br08902
    br:br08904
    br:br08906
    br:ko00001
    br:ko00002
    br:ko00003
    br:br08907
    br:ko01000
    br:ko01001


.. code:: none

    % kegg_pull entry-ids molec-attr drug --em=433 --em=434


.. parsed-literal::

    dr:D00752
    dr:D00892
    dr:D02110
    dr:D02114
    dr:D02238
    dr:D03088
    dr:D04789
    dr:D05806
    dr:D05911
    dr:D06342
    dr:D07084
    dr:D07761
    dr:D07879
    dr:D08757
    dr:D09567
    dr:D10084
    dr:D10309
    dr:D10661
    dr:D11316


.. code:: none

    % kegg_pull entry-ids keywords compound protein,enzyme


.. parsed-literal::

    cpd:C05197
    cpd:C05312
    cpd:C15972
    cpd:C15973


map
~~~

.. code:: none

    % kegg_pull map link entry-ids path:map00010,path:map00020 compound --output=mapping.json
    % head mapping.json


.. parsed-literal::

    {
      "path:map00010": [
        "cpd:C00022",
        "cpd:C00024",
        "cpd:C00031",
        "cpd:C00033",
        "cpd:C00036",
        "cpd:C00068",
        "cpd:C00074",
        "cpd:C00084",


pathway-organizer
~~~~~~~~~~~~~~~~~

.. code:: none

    % kegg_pull pathway-organizer --tln=Metabolism --fn="Global and overview maps,Carbohydrate metabolism" --output=hierarchy-nodes.json
    % head hierarchy-nodes.json


.. parsed-literal::

    {
      "path:map00190": {
        "name": "00190  Oxidative phosphorylation",
        "level": 3,
        "parent": "Energy metabolism",
        "children": null,
        "entry_id": "path:map00190"
      },
      "path:map00195": {
        "name": "00195  Photosynthesis",


rest
~~~~

.. code:: none

    % kegg_pull rest info enzyme


.. parsed-literal::

    enzyme           KEGG Enzyme Database
    ec               Release 106.0+/04-07, Apr 23
                     Kanehisa Laboratories
                     8,056 entries
    
    linked db        pathway
                     module
                     ko
                     <org>
                     vg
                     vp
                     ag
                     compound
                     glycan
                     reaction
                     rclass
    


.. code:: none

    % kegg_pull rest get cpd:C00007 --entry-field=mol


.. parsed-literal::

     
     
     
      2  1  0  0  0  0  0  0  0  0999 V2000
       24.3446  -17.0048    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
       25.7446  -17.0048    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
      1  2  2  0     0  0
    M  END
    
    > <ENTRY>
    cpd:C00007
    
    $$$$
    


.. code:: none

    % kegg_pull rest conv entry-ids gl:G13143,gl:G13141,gl:G13139 pubchem


.. parsed-literal::

    gl:G13143	pubchem:405226698
    gl:G13141	pubchem:405226697
    gl:G13139	pubchem:405226696
    


The ``rest`` subcommand additionally offers the ``--test`` option to
determine if a request to the KEGG REST API will fail or pass before
actually executing the command.

.. code:: none

    % kegg_pull rest ddi invalid-drug-entry-id --test


.. parsed-literal::

    False

