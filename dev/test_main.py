import kegg_pull.__main__ as m
import kegg_pull.entry_ids_cli as ei_cli
import kegg_pull.rest_cli as r_cli
import kegg_pull.pull_cli as p_cli


def test_main_help(mocker):
    mocker.patch('sys.argv', ['kegg_pull', '--full-help'])
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    m.main()
    print_mock.assert_any_call(m.__doc__)
    print_mock.assert_any_call(ei_cli.__doc__)
    print_mock.assert_any_call(r_cli.__doc__)
    print_mock.assert_any_call(p_cli.__doc__)
    mocker.patch('sys.argv', ['kegg_pull', '--help'])
    print_mock.reset_mock()
    m.main()
    print_mock.assert_called_once_with(m.__doc__)
    print_mock.reset_mock()
    mocker.patch('sys.argv', ['kegg_pull'])
    m.main()
    print_mock.assert_called_once_with(m.__doc__)


# TODO: Test subcommands
