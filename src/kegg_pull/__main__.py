"""
Usage:
    kegg_pull entry-ids from-database (--database-name=<database-name>) [--output=<output>]
    kegg_pull entry-ids from-file (--entry-ids-file-path=<entry-ids-file-path>) [--output=<output>]
    kegg_pull entry-ids from-keywords (--database-name=<database-name>) (--keywords=<keywords>) [--output=<output>]
    kegg_pull entry-ids from-molecular-attribute (--database-name=<database-name>) (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>]
    kegg_pull multiple (--database-name=<database-name>|--entry-ids-file-path=<entry-ids-file-path>) [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output-dir=<output_dir>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]
    kegg_pull single (--entry-ids=<entry-ids>|--entry-ids-file-path=<entry-ids-file-path>) [--output-dir=<output_dir>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]

Options:
    -h --help                                       Show this help message
    entry-ids                                       Obtains a list of KEGG entry IDs.
    from-database                                   Gets all the entry IDs within a given database.
    --database-name=<database-name>                 The KEGG database from which to get a list of entry IDs. If used with "kegg_pull multiple", the entries associated with the obtained IDs are then pulled.
    --output=<output>                               Path to the file to store the output. Prints to the console if not specified.
    from-file                                       Loads the entry IDs from a file.
    --entry-ids-file-path=<entry-ids-file-path>     Path to a file containing a list of entry IDs with one entry ID on each line.
    from-keywords                                   Searches for entries within a database based on provided key words.
    --keywords=<keywords>                           Comma separated list of keywords to search within entries (e.g. --keywords=kw1,k2w,kw3 etc.).
    from-molecular-attribute                        Searches a database of molecule-type KEGG entries by molecular attributes.
    --formula=<formula>                             Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searchers for molecule entries containing 5 oxygen atoms or 7 carbon atoms).
    --exact-mass=<exact-mass>                       Either a single number (e.g. --exact-mass=100) or two numbers (e.g. --exact-mass=100 --exact-mass=200). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
    --molecular-weight=<molecular-weight>           Same as --exact-mass but searches based on the molecular weight.
    multiple                                        Pull, separate, and store as many entries as requested via multiple automated requests to the KEGG web API. Useful when the number of entries requested is well above the maximum that KEGG allows for a single request.
    --force-single-entry                            Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if --database-name is "brite".
    --multi-process                                 If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
    --n-workers=<n-workers>                         The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
    --output-dir=<output_dir>                       The directory where the pulled KEGG entries will be stored. Defaults to the current working directory.
    --entry-field=<entry-field>                     Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
    --n-tries=<n-tries>                             The number of times to attempt a KEGG request before marking it as timed out or failed.
    --time-out=<time-out>                           The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 0.
    --sleep-time=<sleep-time>                       The amount of time to wait after a KEGG request times out before attempting it again. Defaults to 60.
    single                                          Pull, separate, and store one or more KEGG entries via a single request to the KEGG web API. Useful when the number of entries requested is less than or equal to the maximum that KEGG allows for a single request.
    --entry-ids=<entry-ids>                         Comma separated list of entry IDs to pull in a single request (e.g. --entry-ids=id1,id2,id3 etc.).
"""
import docopt as d
import logging as l
import typing as t

from . import kegg_request as kr
from . import pull as p
from . import get_entry_ids as ge


def main():
    args: dict = d.docopt(__doc__)
    database_name: str = args['--database-name']
    entry_ids_file_path: str = args['--entry-ids-file-path']
    output: str = args['--output']

    if args['entry-ids']:
        if args['from-database']:
            entry_ids: list = ge.from_database(database_name=database_name)
        elif args['from-file']:
            entry_ids: list = ge.from_file(entry_ids_file_path=entry_ids_file_path)
        elif args['from-keywords']:
            keywords: str = args['--keywords']
            keywords: list = _split_comma_separated_list(list_string=keywords)
            entry_ids: list = ge.from_keywords(database_name=database_name, keywords=keywords)
        else:
            formula: str = args['--formula']
            exact_mass: list = args['--exact-mass']
            molecular_weight: list = args['--molecular-weight']

            if exact_mass is not None:
                exact_mass: t.Union[float, tuple] = _get_range_values(range_values=exact_mass, value_type=float)

            if molecular_weight is not None:
                molecular_weight: t.Union[int, tuple] = _get_range_values(range_values=molecular_weight, value_type=int)

            entry_ids: list = ge.from_molecular_attribute(
                database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
            )


        if output is not None:
            with open(output, 'w') as f:
                for entry_id in entry_ids:
                    f.write(entry_id + '\n')
        else:
            for entry_id in entry_ids:
                print(entry_id)
    else:
        n_tries: str = int(args['--n-tries']) if args['--n-tries'] is not None else None
        time_out: str = int(args['--time-out']) if args['--time-out'] is not None else None
        sleep_time: str = float(args['--sleep-time']) if args['--sleep-time'] is not None else None
        kegg_request = kr.KEGGrequest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
        output_dir: str = args['--output-dir'] if args['--output-dir'] is not None else '.'
        entry_field: str = args['--entry-field']
        puller = p.SinglePull(output_dir=output_dir, kegg_request=kegg_request, entry_field=entry_field)
        force_single_entry: bool = args['--force-single-entry']

        if database_name is not None:
            if database_name == 'brite':
                force_single_entry = True

            entry_ids: list = ge.from_database(database_name=database_name)
        elif args['--entry-ids-path'] is not None:
            entry_ids: list = ge.from_file(entry_ids_file_path=entry_ids_file_path)
        else:
            entry_ids_string: str = args['--entry-ids']
            entry_ids: list = _split_comma_separated_list(list_string=entry_ids_string)

        if args['multiple']:
            if args['--multi-process']:
                n_workers = int(args['--n-workers']) if args['--n-workers'] is not None else None

                puller = p.MultiProcessMultiplePull(
                    single_pull=puller, force_single_entry=force_single_entry, n_workers=n_workers
                )
            else:
                puller = p.SingleProcessMultiplePull(single_pull=puller, force_single_entry=force_single_entry)

        pull_result: p.PullResult = puller.pull(entry_ids=entry_ids)

        with open('pull-results.txt', 'w') as f:
            _write_entry_ids(f=f, entry_id_type='Successful', entry_ids=pull_result.successful_entry_ids)
            _write_entry_ids(f=f, entry_id_type='Failed', entry_ids=pull_result.failed_entry_ids)
            _write_entry_ids(f=f, entry_id_type='Timed Out', entry_ids=pull_result.timed_out_entry_ids)


def _split_comma_separated_list(list_string: str) -> list:
    items: list = list_string.split(',')

    if '' in items:
        l.warning(f'Blank items detected in the comma separated list: "{list_string}". Removing blanks...')
        items = [entry_id for entry_id in items if entry_id != '']

    return items


def _get_range_values(range_values: t.Union[int, float, tuple], value_type: type) -> t.Union[int, float, tuple]:
    if len(range_values) == 1:
        [val] = range_values

        return value_type(val)
    elif len(range_values) == 2:
        [min_val, max_val] = range_values

        return value_type(min_val), value_type(max_val)
    else:
        raise ValueError(
            f'Range can only be specified by two values but {len(range_values)} values were provided: '
            f'{", ".join(range_values)}'
        )


def _write_entry_ids(f, entry_id_type: str, entry_ids: list):
    f.write(f'### {entry_id_type} Entry IDs ###\n')

    for entry_id in entry_ids:
        f.write(entry_id + '\n')


if __name__ == '__main__':
    main()
