"""
Usage:
    kegg_pull pull -h | --help
    kegg_pull pull multiple (--database-name=<database-name>|--file-path=<file-path>) [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output=<output>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]
    kegg_pull pull single (--entry-ids=<entry-ids>|--file-path=<file-path>) [--output=<output>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]

Options:
    -h --help                           Show this help message.
    multiple                            Pull, separate, and store as many entries as requested via multiple automated requests to the KEGG web API. Useful when the number of entries requested is well above the maximum that KEGG allows for a single request.
    --database-name=<database-name>     The KEGG database from which to pull a list of IDs of entries to then pull.
    --file-path=<file-path>             Path to a file containing a list of entry IDs to pull, with one entry ID on each line. Will likely need to set --force-single-entry if any of the entries are from the brite database.
    --force-single-entry                Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if --database-name is "brite".
    --multi-process                     If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
    --n-workers=<n-workers>             The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
    --output=<output>                   The directory where the pulled KEGG entries will be stored. Defaults to the current working directory. If ends in .zip, entries are saved to a zip archive instead of a directory.
    --entry-field=<entry-field>         Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
    --n-tries=<n-tries>                 The number of times to attempt a KEGG request before marking it as timed out or failed. Defaults to 3.
    --time-out=<time-out>               The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 60.
    --sleep-time=<sleep-time>           The amount of time to wait after a KEGG request times out (or potentially blacklists with a 403 error code) before attempting it again. Defaults to 10.0.
    single                              Pull, separate, and store one or more KEGG entries via a single request to the KEGG web API. Useful when the number of entries requested is less than or equal to the maximum that KEGG allows for a single request.
    --entry-ids=<entry-ids>             Comma separated list of entry IDs to pull in a single request (e.g. --entry-ids=id1,id2,id3 etc.).
"""
import docopt as d
import json as j
import time as t

from . import pull as p
from . import rest as r
from . import entry_ids as ei
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    n_tries: str = int(args['--n-tries']) if args['--n-tries'] is not None else None
    time_out: str = int(args['--time-out']) if args['--time-out'] is not None else None
    sleep_time: str = float(args['--sleep-time']) if args['--sleep-time'] is not None else None
    kegg_rest = r.KEGGrest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    output_dir: str = args['--output'] if args['--output'] is not None else '.'
    entry_field: str = args['--entry-field']
    puller = p.SinglePull(output_dir=output_dir, kegg_rest=kegg_rest, entry_field=entry_field)
    database_name: str = args['--database-name']
    force_single_entry: bool = args['--force-single-entry']

    if database_name is not None:
        if database_name == 'brite':
            force_single_entry = True

        entry_ids_getter = ei.EntryIdsGetter(kegg_rest=kegg_rest)
        entry_ids: list = entry_ids_getter.from_database(database_name=database_name)
    elif args['--file-path'] is not None:
        file_path: str = args['--file-path']
        entry_ids: list = ei.EntryIdsGetter.from_file(file_path=file_path)
    else:
        entry_ids_string: str = args['--entry-ids']
        entry_ids: list = u.split_comma_separated_list(list_string=entry_ids_string)

    if args['multiple']:
        if args['--multi-process']:
            n_workers = int(args['--n-workers']) if args['--n-workers'] is not None else None

            puller = p.MultiProcessMultiplePull(
                single_pull=puller, force_single_entry=force_single_entry, n_workers=n_workers
            )
        else:
            puller = p.SingleProcessMultiplePull(single_pull=puller, force_single_entry=force_single_entry)

    t1: float = _testable_time()
    pull_result: p.PullResult = puller.pull(entry_ids=entry_ids)
    t2: float = _testable_time()

    total_entry_ids: int = len(pull_result.successful_entry_ids) + len(pull_result.failed_entry_ids)
    total_entry_ids += len(pull_result.timed_out_entry_ids)
    success_rate: float = len(pull_result.successful_entry_ids) / total_entry_ids * 100

    pull_results = {
        'percent-success': float(f'{success_rate:.2f}'),
        'pull-minutes': float(f'{(t2 - t1) / 60:.2f}'),
        'num-successful': len(pull_result.successful_entry_ids),
        'num-failed': len(pull_result.failed_entry_ids),
        'num-timed-out': len(pull_result.timed_out_entry_ids),
        'num-total': total_entry_ids,
        'successful-entry-ids': pull_result.successful_entry_ids,
        'failed-entry-ids': pull_result.failed_entry_ids,
        'timed-out-entry-ids': pull_result.timed_out_entry_ids
    }

    with open('pull-results.json', 'w') as file:
        j.dump(pull_results, file, indent=0)


def _testable_time() -> float:
    """ The time.time() function causes issues when mocked in tests, so we create this wrapper that can be safely mocked

    :return: The result of time.time()
    """
    return t.time()  # pragma: no cover
