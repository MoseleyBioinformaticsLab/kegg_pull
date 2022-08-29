"""
Usage:
    kegg_pull -h | --help       Show this help message.
    kegg_pull --full-help       Show the help message of all sub commands.
    kegg_pull entry-ids ...     Obtain a list of KEGG entry IDs.
    kegg_pull rest ...          Executes one of the KEGG REST API operations.
    kegg_pull pull ...          Pull, separate, and store KEGG entries to the local file system.
"""
import sys

from . import entry_ids as ei
from . import rest as r
from . import pull as p


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'entry-ids':
        ei.main()
    elif len(sys.argv) > 1 and sys.argv[1] == 'rest':
        r.main()
    elif len(sys.argv) > 1 and sys.argv[1] == 'pull':
        p.main()
    elif len(sys.argv) > 1 and sys.argv[1] == '--full-help':
        separator = '-'*80
        print(__doc__)
        print(separator)
        print(ei.__doc__)
        print(separator)
        print(r.__doc__)
        print(separator)
        print(p.__doc__)
    else:
        print(__doc__)


if __name__ == '__main__':  # pragma: no cover
    main()  # pragma: no cover
