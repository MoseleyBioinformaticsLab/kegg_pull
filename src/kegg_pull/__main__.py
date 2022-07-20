"""
Usage:
    kegg_pull <output_dir> (--database-type=<database-type>|--entry-id-list-path=<entry-id-list-path>)
    [--entry-field=<entry-field>] [--n-workers=<n-workers>] [--force-single-entry]

Options:
    -h --help                                   Show this help message
    --database-type=<database-type>             The KEGG database from which to get a list of entry IDs to pull
    --entry-id-list-path=<entry-id-list-path>   Path to a file containing a list of entry IDs with one entry ID on each line (used if a --database-type is not provided)
    --entry-field=<entry-field>                 Optional field to extract from the entries pulled rather than the standard flat file format or "htext" in the case of brite entries
    --n-workers=<n-workers>                     The number of sub-processes to create when pulling. Defaults to the number of cores available
    --force-single-entry                        Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if --database-type is "brite"
"""
import docopt as d

from . import multiple_pull as mp


def main():
    args: dict = d.docopt(__doc__)
    print(args)
    output_dir: str = args['<output_dir>']
    database_type: str = args['--database-type']
    entry_id_list_path: str = args['--entry-id-list-path']
    entry_field: str = args['--entry-field']
    n_workers: str = args['--n-workers']
    force_single_entry: bool = args['--force-single-entry']
    n_workers: int = int(n_workers) if n_workers is not None else None

    mp.multiple_pull(
        output_dir=output_dir, database_type=database_type, entry_id_list_path=entry_id_list_path,
        entry_field=entry_field, n_workers=n_workers, force_single_entry=force_single_entry
    )


if __name__ == '__main__':
    main()
