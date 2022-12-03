import pytest as pt

def assert_expected_error_message(expected_message: str, error: pt.ExceptionInfo):
    actual_message = str(error.value)

    assert actual_message == expected_message


def assert_warning(message: str, caplog):
    [record] = caplog.records

    assert record.levelname == 'WARNING'
    assert record.message == message


def assert_error(message: str, caplog):
    [record] = caplog.records

    assert record.levelname == 'ERROR'
    assert record.message == message


def assert_main_help(mocker, module, subcommand: str):
    mocker.patch('sys.argv', ['kegg_pull', subcommand, '--help'])
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')

    with pt.raises(SystemExit):
        module.main()

    print_mock.assert_any_call(module.__doc__.strip('\n'))
    

def assert_call_args(function_mock, expected_call_args_list: list, do_kwargs: bool):
    actual_call_args_list = function_mock.call_args_list
    
    for actual_call_args, expected_call_args in zip(actual_call_args_list, expected_call_args_list):
        if do_kwargs:
            assert actual_call_args.kwargs == expected_call_args
        else:
            assert actual_call_args.args == expected_call_args
