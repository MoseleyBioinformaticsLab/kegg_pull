import pytest as pt

def assert_expected_error_message(expected_message: str, error: pt.ExceptionInfo):
    actual_message = str(error.value)

    assert actual_message == expected_message


def assert_warning(message: str, caplog):
    [record] = caplog.records

    assert record.levelname == 'WARNING'
    assert record.message == message
