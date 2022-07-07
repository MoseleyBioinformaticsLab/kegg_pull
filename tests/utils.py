from pytest import ExceptionInfo


def assert_expected_error_message(expected_message: str, e: ExceptionInfo):
    actual_message: str = str(e.value)

    assert actual_message == expected_message


def assert_warning(file_name: str, func_name: str, message: str, caplog: iter):
    [record] = caplog.records

    assert record.levelname == 'WARNING'
    assert record.filename == file_name
    assert record.funcName == func_name
    assert record.message == message