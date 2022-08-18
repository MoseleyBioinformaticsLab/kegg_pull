import pytest as pt

def assert_expected_error_message(expected_message: str, error: pt.ExceptionInfo):
    actual_message = str(error.value)

    assert actual_message == expected_message


def assert_warning(file_name: str, func_name: str, message: str, caplog):
    [record] = caplog.records

    assert record.levelname == 'WARNING'
    assert record.filename == file_name
    assert record.funcName == func_name
    assert record.message == message
