import pytest as pt
import zipfile as zf
import typing as t
import json as j
import jsonschema as js
import os


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
    for help_arg in ['-h', '--help']:
        mocker.patch('sys.argv', ['kegg_pull', subcommand, help_arg])
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


def _test_main(mocker, argv_mock: list, stdin_mock: str, method: str, method_return_value: object, method_kwargs: dict, module):
    argv_mock: list = ['kegg_pull'] + argv_mock
    mocker.patch('sys.argv', argv_mock)
    stdin_mock: mocker.MagicMock = mocker.patch('kegg_pull._utils.sys.stdin.read', return_value=stdin_mock) if stdin_mock else None

    method_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.{method}', return_value=method_return_value
    )

    module.main()
    method_mock.assert_called_once_with(**method_kwargs)

    if stdin_mock:
        stdin_mock.assert_called_once_with()


def test_main_print(
    mocker, argv_mock: list, stdin_mock: str, method: str, method_return_value: object, method_kwargs: dict, module,
    expected_output: t.Union[str, bytes], is_binary: bool = False, caplog = None
):
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')

    _test_main(
        mocker=mocker, argv_mock=argv_mock, stdin_mock=stdin_mock, method=method, method_return_value=method_return_value,
        method_kwargs=method_kwargs, module=module
    )

    if is_binary:
        assert_warning(message='Printing binary output...', caplog=caplog)

    print_mock.assert_called_once_with(expected_output)


def test_main_file(
    mocker, argv_mock: list, output_file: str, stdin_mock: str, method: str, method_return_value: object, method_kwargs: dict, module,
    expected_output: t.Union[str, bytes], is_binary: bool = False
):
    argv_mock: list = argv_mock + [f'--output={output_file}']

    _test_main(
        mocker=mocker, argv_mock=argv_mock, stdin_mock=stdin_mock, method=method, method_return_value=method_return_value,
        method_kwargs=method_kwargs, module=module
    )

    read_type: str = 'rb' if is_binary else 'r'

    with open(output_file, read_type) as file:
        actual_output: t.Union[str, bytes] = file.read()

    assert actual_output == expected_output


def test_main_zip_archive(
    mocker, argv_mock: list, zip_archive_data: tuple, stdin_mock: str, method: str, method_return_value: object, method_kwargs: dict,
    module, expected_output: t.Union[str, bytes], is_binary: bool = False
):
    zip_archive_path, zip_file_name = zip_archive_data
    argv_mock: list = argv_mock + [f'--output={zip_archive_path}:{zip_file_name}']

    _test_main(
        mocker=mocker, argv_mock=argv_mock, stdin_mock=stdin_mock, method=method, method_return_value=method_return_value,
        method_kwargs=method_kwargs, module=module
    )

    with zf.ZipFile(zip_archive_path, 'r') as zip_file:
        actual_output: bytes = zip_file.read(zip_file_name)

        if not is_binary:
            actual_output: str = actual_output.decode()

    assert actual_output == expected_output


def test_save_to_json(json_file_path: str, expected_saved_json_object: dict):
    if '.zip:' in json_file_path:
        with zf.ZipFile('archive.zip', 'r') as zip_file:
            json_file_name: str = 'dir/file.json' if 'dir/' in json_file_path else 'file.json'
            actual_saved_mapping: dict = j.loads(zip_file.read(name=json_file_name))
    else:
        with open(json_file_path, 'r') as file:
            actual_saved_mapping: dict = j.load(file)

    assert actual_saved_mapping == expected_saved_json_object


def test_load_from_json(
    json_file_path: str, saved_object: dict, method: t.Callable, expected_loaded_object: dict, loaded_object_attribute: str = None
):
    _write_test_json_object(json_file_path=json_file_path, test_object=saved_object)
    actual_loaded_object: t.Union[object, dict] = method(file_path=json_file_path)

    if loaded_object_attribute is not None:
        actual_loaded_object: dict = actual_loaded_object.__getattribute__(loaded_object_attribute)

    assert actual_loaded_object == expected_loaded_object


def _write_test_json_object(json_file_path: str, test_object: t.Union[list, dict, int, float, str]) -> None:
    if '.zip:' in json_file_path:
        with zf.ZipFile('archive.zip', 'w') as zip_file:
            json_file_name: str = 'dir/file.json' if 'dir/' in json_file_path else 'file.json'
            zip_file.writestr(json_file_name, j.dumps(test_object, indent=2))
    else:
        if json_file_path.startswith('dir'):
            directory, _ = os.path.split(json_file_path)
            os.makedirs(directory)

        with open(json_file_path, 'w') as file:
            file.write(j.dumps(test_object, indent=2))


def test_invalid_load_from_json(
    json_file_path: str, invalid_json_object: dict, method: t.Callable, expected_error_message: str, caplog
):
    _write_test_json_object(json_file_path=json_file_path, test_object=invalid_json_object)

    with pt.raises(js.exceptions.ValidationError):
        method(file_path=json_file_path)

    assert_error(message=expected_error_message, caplog=caplog)
