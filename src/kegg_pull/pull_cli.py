"""
Usage:
    kegg_pull pull -h | --help
    kegg_pull pull database <database> [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output=<output>] [--print] [--sep=<print-separator>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>] [--ut=<unsuccessful-threshold>]
    kegg_pull pull entry-ids <entry-ids> [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output=<output>] [--print] [--sep=<print-separator>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>] [--ut=<unsuccessful-threshold>]

Options:
    -h --help                       Show this help message.
    database                        Pulls all the entries in a KEGG database.
    <database>                      The KEGG database from which to pull entries.
    --force-single-entry            Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if <database> is "brite".
    --multi-process                 If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
    --n-workers=<n-workers>         The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
    --output=<output>               The directory where the pulled KEGG entries will be stored. Defaults to the current working directory. If ends in ".zip", entries are saved to a ZIP archive instead of a directory. Ignored if --print is set.
    --print                         If set, prints the entries to the screen rather than saving them to the file system. Separates entries by the --sep option if set.
    --sep=<print-separator>         The string that separates the entries which are printed to the screen when the --print option is set. Ignored if the --print option is not set. Defaults to printing the entry id, followed by the entry, followed by a newline.
    --entry-field=<entry-field>     Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
    --n-tries=<n-tries>             The number of times to attempt a KEGG request before marking it as timed out or failed. Defaults to 3.
    --time-out=<time-out>           The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 60.
    --sleep-time=<sleep-time>       The amount of time to wait after a KEGG request times out (or potentially blacklists with a 403 error code) before attempting it again. Defaults to 5.0.
    --ut=<unsuccessful-threshold>   If set, the ratio of unsuccessful entry IDs (failed or timed out) to total entry IDs at which kegg_pull quits. Valid values are between 0.0 and 1.0 non-inclusive.
    entry-ids                       Pulls entries specified by a comma separated list. Or from standard input: one entry ID per line; Press CTRL+D to finalize input or pipe (e.g. cat file.txt | kegg_pull pull entry-ids - ...).
    <entry-ids>                     Comma separated list of entry IDs to pull (e.g. id1,id2,id3 etc.). Or if equal to "-", entry IDs are read from standard input. Will likely need to set --force-single-entry if any of the entries are from the brite database.
"""
import docopt as d
import json
import time
import logging as log
from . import pull as p
from . import rest as r
from . import entry_ids as ei
from . import kegg_url as ku
from . import _utils as u


def main():
    args = d.docopt(__doc__)
    n_tries = int(args['--n-tries']) if args['--n-tries'] is not None else None
    time_out = int(args['--time-out']) if args['--time-out'] is not None else None
    sleep_time = float(args['--sleep-time']) if args['--sleep-time'] is not None else None
    kegg_rest = r.KEGGrest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    output = args['--output'] if args['--output'] is not None else '.'
    print_to_screen: bool = args['--print']
    entry_field: str = args['--entry-field']
    force_single_entry: bool = args['--force-single-entry']
    if args['database']:
        database: str = args['<database>']
        if database == 'brite':
            force_single_entry = True
        entry_ids = ei.from_database(database=database)
    else:
        entry_ids = u.parse_input_sequence(input_source=args['<entry-ids>'])
    unsuccessful_threshold = float(args['--ut']) if args['--ut'] is not None else None
    if args['--multi-process']:
        n_workers = int(args['--n-workers']) if args['--n-workers'] is not None else None
        multiple_pull = p.MultiProcessMultiplePull(kegg_rest=kegg_rest, unsuccessful_threshold=unsuccessful_threshold, n_workers=n_workers)
    else:
        multiple_pull = p.SingleProcessMultiplePull(kegg_rest=kegg_rest, unsuccessful_threshold=unsuccessful_threshold)
    time1 = _testable_time()
    if print_to_screen:
        pull_result, kegg_entry_mapping = multiple_pull.pull_dict(
            entry_ids=entry_ids, entry_field=entry_field, force_single_entry=force_single_entry)
        if ku.GetKEGGurl.is_binary(entry_field=entry_field):
            log.warning('Printing binary output...')
        print_separator: str = args['--sep']
        if print_separator:
            print(f'\n{print_separator}\n'.join(kegg_entry_mapping.values()))
        else:
            for entry_id, entry in kegg_entry_mapping.items():
                print(entry_id)
                print(f'{entry}\n')
    else:
        pull_result = multiple_pull.pull(entry_ids=entry_ids, output=output, entry_field=entry_field, force_single_entry=force_single_entry)
    time2 = _testable_time()
    n_total_entry_ids = len(pull_result.successful_entry_ids) + len(pull_result.failed_entry_ids)
    n_total_entry_ids += len(pull_result.timed_out_entry_ids)
    percent_success = len(pull_result.successful_entry_ids) / n_total_entry_ids * 100
    pull_results = {
        'percent-success': float(f'{percent_success:.2f}'),
        'pull-minutes': float(f'{(time2 - time1) / 60:.2f}'),
        'num-successful': len(pull_result.successful_entry_ids),
        'num-failed': len(pull_result.failed_entry_ids),
        'num-timed-out': len(pull_result.timed_out_entry_ids),
        'num-total': n_total_entry_ids,
        'successful-entry-ids': pull_result.successful_entry_ids,
        'failed-entry-ids': pull_result.failed_entry_ids,
        'timed-out-entry-ids': pull_result.timed_out_entry_ids}
    with open('pull-results.json', 'w') as file:
        json.dump(pull_results, file, indent=0)


def _testable_time() -> float:
    """ The time.time() function causes issues when mocked in tests, so we create this wrapper that can be safely mocked

    :return: The result of time.time()
    """
    return time.time()  # pragma: no cover
