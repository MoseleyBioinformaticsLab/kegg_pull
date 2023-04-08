"""
Usage:
    kegg_pull -h | --help           Show this help message.
    kegg_pull -v | --version        Displays the package version.
    kegg_pull --full-help           Show the help message of all sub commands.
    kegg_pull pull ...              Pull, separate, and store an arbitrary number of KEGG entries to the local file system.
    kegg_pull entry-ids ...         Obtain a list of KEGG entry IDs.
    kegg_pull map ...               Obtain a mapping of entry IDs (KEGG or outside databases) to the IDs of related entries.
    kegg_pull rest ...              Executes one of the KEGG REST API operations.
"""
import sys
from . import __version__
from . import pull_cli as p_cli
from . import entry_ids_cli as ei_cli
from . import map_cli as map_cli
from . import rest_cli as r_cli


def main() -> None:
    first_arg: str = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg == 'pull':
        p_cli.main()
    elif first_arg == 'entry-ids':
        ei_cli.main()
    elif first_arg == 'map':
        map_cli.main()
    elif first_arg == 'rest':
        r_cli.main()
    elif first_arg == '--full-help':
        separator = '-'*80
        print(__doc__)
        print(separator)
        print(p_cli.__doc__)
        print(separator)
        print(ei_cli.__doc__)
        print(separator)
        print(map_cli.__doc__)
        print(separator)
        print(r_cli.__doc__)
    elif first_arg == '--version' or first_arg == '-v':
        print(__version__)
    else:
        print(__doc__)


if __name__ == '__main__':  # pragma: no cover
    main()  # pragma: no cover
