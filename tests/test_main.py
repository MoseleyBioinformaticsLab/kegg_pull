import kegg_pull.__main__ as m
import kegg_pull.entry_ids as ei
import kegg_pull.rest as r
import kegg_pull.pull as p


def test_main_help(mocker):
    mocker.patch('sys.argv', ['kegg_pull', '--full-help'])
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    m.main()
    print_mock.assert_any_call(m.__doc__)
    print_mock.assert_any_call(ei.__doc__)
    print_mock.assert_any_call(r.__doc__)
    print_mock.assert_any_call(p.__doc__)
    mocker.patch('sys.argv', ['kegg_pull', '--help'])
    print_mock.reset_mock()
    m.main()
    print_mock.assert_called_once_with(m.__doc__)
    print_mock.reset_mock()
    mocker.patch('sys.argv', ['kegg_pull'])
    m.main()
    print_mock.assert_called_once_with(m.__doc__)


# TODO: Test subcommands
