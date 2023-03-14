import pytest as pt

def assert_expected_error_message(expected_message: str, error: pt.ExceptionInfo):
    actual_message = str(error.value)

    assert actual_message == expected_message


def assert_warning(message: str, caplog):
    [record] = caplog.records

    assert record.levelname == 'WARNING'
    assert record.message == message


def assert_cli_help(mocker, module, subcommand: str):
    mocker.patch('sys.argv', ['kegg_pull', subcommand, '--help'])
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')

    with pt.raises(SystemExit):
        module.main()

    print_mock.assert_any_call(module.__doc__.strip('\n'))
