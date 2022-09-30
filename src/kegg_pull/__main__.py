"""
Usage:
    kegg_pull -h | --help       Show this help message.
    kegg_pull -v | --version    Displays the package version.
    kegg_pull --full-help       Show the help message of all sub commands.
    kegg_pull entry-ids ...     Obtain a list of KEGG entry IDs.
    kegg_pull rest ...          Executes one of the KEGG REST API operations.
    kegg_pull pull ...          Pull, separate, and store KEGG entries to the local file system.
"""
import sys

from . import __version__
from . import entry_ids_cli as ei_cli
from . import rest_cli as r_cli
from . import pull_cli as p_cli


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'entry-ids':
        ei_cli.main()
    elif len(sys.argv) > 1 and sys.argv[1] == 'rest':
        r_cli.main()
    elif len(sys.argv) > 1 and sys.argv[1] == 'pull':
        p_cli.main()
    elif len(sys.argv) > 1 and sys.argv[1] == '--full-help':
        separator = '-'*80
        print(__doc__)
        print(separator)
        print(ei_cli.__doc__)
        print(separator)
        print(r_cli.__doc__)
        print(separator)
        print(p_cli.__doc__)
    elif len(sys.argv) > 1 and (sys.argv[1] == '--version' or sys.argv[1] == '-v'):
        print(__version__)
    else:
        print(__doc__)


if __name__ == '__main__':  # pragma: no cover
    main()  # pragma: no cover
