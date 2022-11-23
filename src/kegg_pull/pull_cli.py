"""
Usage:
    kegg_pull pull -h | --help
    kegg_pull pull database <database-name> [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output=<output>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>] [--ut=<unsuccessful-threshold>]
    kegg_pull pull entry-ids <entry-ids> [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output=<output>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>] [--ut=<unsuccessful-threshold>]

Options:
    -h --help                       Show this help message.
    database                        Pulls all the entries in a KEGG database.
    <database-name>                 The KEGG database from which to pull entries.
    --force-single-entry            Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if <database-name> is "brite".
    --multi-process                 If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
    --n-workers=<n-workers>         The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
    --output=<output>               The directory where the pulled KEGG entries will be stored. Defaults to the current working directory. If ends in ".zip", entries are saved to a ZIP archive instead of a directory.
    --entry-field=<entry-field>     Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
    --n-tries=<n-tries>             The number of times to attempt a KEGG request before marking it as timed out or failed. Defaults to 3.
    --time-out=<time-out>           The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 60.
    --sleep-time=<sleep-time>       The amount of time to wait after a KEGG request times out (or potentially blacklists with a 403 error code) before attempting it again. Defaults to 5.0.
    --ut=<unsuccessful-threshold>   If set, the ratio of unsuccessful entry IDs (failed or timed out) to total entry IDs at which kegg_pull quits. Valid values are between 0.0 and 1.0 non-inclusive.
    entry-ids                       Pulls entries specified by a comma separated list. Or from standard input: one entry ID per line; Press CTRL+D to finalize input or pipe (e.g. cat file.txt | kegg_pull pull entry-ids - ...).
    <entry-ids>                     Comma separated list of entry IDs to pull (e.g. id1,id2,id3 etc.). Or if equal to "-", entry IDs are read from standard input. Will likely need to set --force-single-entry if any of the entries are from the brite database.
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
    n_tries: int = int(args['--n-tries']) if args['--n-tries'] is not None else None
    time_out: int = int(args['--time-out']) if args['--time-out'] is not None else None
    sleep_time: float = float(args['--sleep-time']) if args['--sleep-time'] is not None else None
    kegg_rest = r.KEGGrest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    output: str = args['--output'] if args['--output'] is not None else '.'
    entry_field: str = args['--entry-field']
    multiprocess_lock_save: bool = args['--multi-process'] and output.endswith('.zip')
    single_pull = p.SinglePull(output=output, kegg_rest=kegg_rest, entry_field=entry_field, multiprocess_lock_save=multiprocess_lock_save)
    force_single_entry: bool = args['--force-single-entry']

    if args['database']:
        database_name: str = args['<database-name>']

        if database_name == 'brite':
            force_single_entry = True

        entry_ids: list = ei.from_database(database_name=database_name)
    else:
        entry_ids: list = u.handle_cli_input(input_source=args['<entry-ids>'])

    unsuccessful_threshold: float = float(args['--ut']) if args['--ut'] is not None else None

    if args['--multi-process']:
        n_workers = int(args['--n-workers']) if args['--n-workers'] is not None else None

        multiple_pull = p.MultiProcessMultiplePull(
            single_pull=single_pull, force_single_entry=force_single_entry, n_workers=n_workers,
            unsuccessful_threshold=unsuccessful_threshold
        )
    else:
        multiple_pull = p.SingleProcessMultiplePull(
            single_pull=single_pull, force_single_entry=force_single_entry, unsuccessful_threshold=unsuccessful_threshold
        )

    time1: float = _testable_time()
    pull_result: p.PullResult = multiple_pull.pull(entry_ids=entry_ids)
    time2: float = _testable_time()

    n_total_entry_ids: int = len(pull_result.successful_entry_ids) + len(pull_result.failed_entry_ids)
    n_total_entry_ids += len(pull_result.timed_out_entry_ids)
    percent_success: float = len(pull_result.successful_entry_ids) / n_total_entry_ids * 100

    pull_results = {
        'percent-success': float(f'{percent_success:.2f}'),
        'pull-minutes': float(f'{(time2 - time1) / 60:.2f}'),
        'num-successful': len(pull_result.successful_entry_ids),
        'num-failed': len(pull_result.failed_entry_ids),
        'num-timed-out': len(pull_result.timed_out_entry_ids),
        'num-total': n_total_entry_ids,
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
