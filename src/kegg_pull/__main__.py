"""
Usage:
    kegg_pull -h | --help           Show this help message.
    kegg_pull -v | --version        Displays the package version.
    kegg_pull --full-help           Show the help message of all sub commands.
    kegg_pull pull ...              Pull, separate, and store an arbitrary number of KEGG entries to the local file system.
    kegg_pull entry-ids ...         Obtain a list of KEGG entry IDs.
    kegg_pull link-to-dict ...      Obtain a mapping of KEGG entries to the IDs of related entries.
    kegg_pull pathway-organizer ... Creates a flattened version of a pathways Brite hierarchy.
    kegg_pull rest ...              Executes one of the KEGG REST API operations.
"""
import sys

from . import __version__
from . import pull_cli as p_cli
from . import entry_ids_cli as ei_cli
from . import link_to_dict_cli as ltd_cli
from . import pathway_organizer_cli as po_cli
from . import rest_cli as r_cli


def main():
    args_provided: bool = len(sys.argv) > 1
    first_arg: str = sys.argv[1]

    if args_provided and first_arg == 'pull':
        p_cli.main()
    elif args_provided and first_arg == 'entry-ids':
        ei_cli.main()
    elif args_provided and first_arg == 'link-to-dict':
        ltd_cli.main()
    elif args_provided and first_arg == 'pathway-organizer':
        po_cli.main()
    elif args_provided and first_arg == 'rest':
        r_cli.main()
    elif args_provided and first_arg == '--full-help':
        separator = '-'*80
        print(__doc__)
        print(separator)
        print(p_cli.__doc__)
        print(separator)
        print(ei_cli.__doc__)
        print(separator)
        print(ltd_cli.__doc__)
        print(separator)
        print(po_cli.__doc__)
        print(separator)
        print(r_cli.__doc__)
    elif args_provided and (first_arg == '--version' or first_arg == '-v'):
        print(__version__)
    else:
        print(__doc__)


if __name__ == '__main__':  # pragma: no cover
    main()  # pragma: no cover
