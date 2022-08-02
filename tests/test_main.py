import kegg_pull.__main__ as m
import kegg_pull.entry_ids as ei
import kegg_pull.pull as p


# TODO: Test subcommand calls
def test_main(mocker):
    mocker.patch('sys.argv', ['kegg_pull', '--full-help'])
    mock_print: mocker.MagicMock = mocker.patch('builtins.print')
    m.main()
    mock_print.assert_any_call(ei.__doc__)
    mock_print.assert_any_call(p.__doc__)
    mocker.patch('sys.argv', ['kegg_pull', '--help'])
    mock_print.reset_mock()
    m.main()
    mock_print.assert_called_once_with(m.__doc__)
    mock_print.reset_mock()
    mocker.patch('sys.argv', ['kegg_pull'])
    m.main()
    mock_print.assert_called_once_with(m.__doc__)
