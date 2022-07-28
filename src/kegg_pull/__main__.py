"""
Usage:
    kegg_pull multiple (--database-name=<database-name>|--entry-ids-file-path=<entry-ids-file-path>) [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output-dir=<output_dir>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]
    kegg_pull single (--entry-ids=<entry-ids>|--entry-ids-file-path=<entry-ids-file-path>) [--output-dir=<output_dir>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>]

Options:
    -h --help                                       Show this help message
    multiple                                        Make multiple requests to the KEGG web API given a list of entry IDs with no limit in length.
    single                                          Make a single request to the KEGG web API with a limited amount of entries.
    --database-name=<database-name>                 The KEGG database from which to get a list of entry IDs to pull.
    --entry-ids-file-path=<entry-ids-file-path>     Path to a file containing a list of entry IDs with one entry ID on each line.
    --force-single-entry                            Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if --database-name is "brite".
    --multi-process                                 If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
    --n-workers=<n-workers>                         The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
    --entry-ids=<entry-ids>                         Comma separated list of entry IDs to pull in a single request (e.g. --entry-ids=id1,id2,id3 etc.).
    --output-dir=<output_dir>                       The directory where the pulled KEGG entries will be stored. Defaults to the current working directory.
    --entry-field=<entry-field>                     Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
    --n-tries=<n-tries>                             The number of times to attempt a KEGG request before marking it as timed out or failed.
    --time-out=<time-out>                           The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 0.
    --sleep-time=<sleep-time>                       The amount of time to wait after a KEGG request times out before attempting it again. Defaults to 60.
"""
import docopt as d

from . import kegg_request as kr
from . import single_pull as sp
from . import pull_result as pr
from . import get_entry_ids as ge
from . import multiple_pull as mp


def main():
    args: dict = d.docopt(__doc__)
    n_tries: str = int(args['--n-tries']) if args['--n-tries'] is not None else None
    time_out: str = int(args['--time-out']) if args['--time-out'] is not None else None
    sleep_time: str = float(args['--sleep-time']) if args['--sleep-time'] is not None else None
    kegg_request = kr.KEGGrequest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    output_dir: str = args['--output-dir'] if args['--output-dir'] is not None else '.'
    entry_field: str = args['--entry-field']
    puller = sp.SinglePull(output_dir=output_dir, kegg_request=kegg_request, entry_field=entry_field)
    database_name: str = args['--database-name']
    force_single_entry: bool = args['--force-single-entry']

    if database_name is not None:
        if database_name == 'brite':
            force_single_entry = True

        entry_ids: list = ge.from_database(database_name=database_name)
    elif args['--entry-ids-path'] is not None:
        entry_ids_file_path: str = args['--entry-ids-file-path']
        entry_ids: list = ge.from_file(file_path=entry_ids_file_path)
    else:
        entry_ids_string: str = args['--entry-ids']
        entry_ids: list = ge.from_string(entry_ids_string=entry_ids_string)

    if args['multiple']:
        if args['--multi-process']:
            n_workers = int(args['--n-workers']) if args['--n-workers'] is not None else None

            puller = mp.MultiProcessMultiplePull(
                single_pull=puller, force_single_entry=force_single_entry, n_workers=n_workers
            )
        else:
            puller = mp.SingleProcessMultiplePull(single_pull=puller, force_single_entry=force_single_entry)

    pull_result: pr.PullResult = puller.pull(entry_ids=entry_ids)

    with open('pull-results.txt', 'w') as f:
        _write_entry_ids(f=f, entry_id_type='Successful', entry_ids=pull_result.successful_entry_ids)
        _write_entry_ids(f=f, entry_id_type='Failed', entry_ids=pull_result.failed_entry_ids)
        _write_entry_ids(f=f, entry_id_type='Timed Out', entry_ids=pull_result.timed_out_entry_ids)


def _write_entry_ids(f, entry_id_type: str, entry_ids: list):
    f.write(f'### {entry_id_type} Entry IDs ###\n')

    for entry_id in entry_ids:
        f.write(entry_id + '\n')


if __name__ == '__main__':
    main()
