import kegg_pull.__main__ as m


def test_main(mocker):
    mocker.patch('sys.argv', ['kegg_pull', './mock-output-dir/', '--database-type=mock-database'])
    mock_multiple_pull = mocker.patch('kegg_pull.__main__.mp.multiple_pull')
    m.main()
    mock_multiple_pull.assert_called_once()
