import logging as log
import typing as t
import zipfile as zf
import os
import sys
import json
import jsonschema as js
import inspect as ins


def get_molecular_attribute_args(args: dict) -> tuple[str | None, float | tuple[float, float] | None, int | tuple[int, int] | None]:
    formula: str | None = args['--formula']
    exact_mass: list[str] | None = args['--em']
    molecular_weight: list[str] | None = args['--mw']
    # exact_mass and molecular_weight will be [] (empty list) if not specified in the commandline args
    if exact_mass:
        exact_mass: float | tuple[float, float] = _get_range_values(range_values=exact_mass, value_type=float)
    else:
        exact_mass = None
    if molecular_weight:
        molecular_weight: int | tuple[int, int] = _get_range_values(range_values=molecular_weight, value_type=int)
    else:
        molecular_weight = None
    return formula, exact_mass, molecular_weight


def _get_range_values(
        range_values: list[str], value_type: type[int | float]) -> int | float | tuple[int, int] | tuple[float, float]:
    if len(range_values) == 1:
        [val] = range_values
        return value_type(val)
    elif len(range_values) == 2:
        [min_val, max_val] = range_values
        return value_type(min_val), value_type(max_val)
    else:
        raise ValueError(
            f'Range can only be specified by two values but {len(range_values)} values were provided: '
            f'{", ".join(range_value for range_value in range_values)}')


def load_json_file(file_path: str, json_schema: dict, validation_error_message: str) -> dict:
    if '.zip:' in file_path:
        [file_location, file_name] = file_path.split('.zip:')
        file_location = file_location + '.zip'
        with zf.ZipFile(file_location, 'r') as zip_file:
            json_object: bytes = zip_file.read(file_name)
            json_object: dict = json.loads(s=json_object)
    else:
        with open(file_path, 'r') as file:
            json_object: dict = json.load(file)
    validate_json_object(json_object=json_object, json_schema=json_schema, validation_error_message=validation_error_message)
    return json_object


def validate_json_object(json_object: dict, json_schema: dict, validation_error_message: str) -> None:
    try:
        js.validate(json_object, json_schema)
    except js.exceptions.ValidationError as e:
        log.error(validation_error_message)
        raise e


def parse_input_sequence(input_source: str) -> list[str]:
    if input_source == '-':
        # Read from standard input
        inputs: str = sys.stdin.read()
        inputs: list = inputs.strip().split('\n')
    else:
        # Split a comma separated list
        inputs: list = input_source.split(',')
    inputs: list = [input_string.strip() for input_string in inputs if input_string.strip() != '']
    # If the inputs end up being an empty list
    if not inputs:
        input_source = 'standard input' if input_source == '-' else f'comma separated list: "{input_source}"'
        raise ValueError(f'Empty list provided from {input_source}')
    return inputs


def print_or_save(output_target: str, output_content: str | bytes) -> None:
    if output_target is None:
        if type(output_content) is bytes:
            log.warning('Printing binary output...')
        print(output_content)
    else:
        save_output(output_target=output_target, output_content=output_content)


def save_output(output_target: str, output_content: str | bytes) -> None:
    if '.zip:' in output_target:
        [file_location, file_name] = output_target.split('.zip:')
        file_location: str = file_location + '.zip'
    else:
        file_location, file_name = os.path.split(output_target)
        file_location = '.' if file_location == '' else file_location
    save_file(file_location=file_location, file_content=output_content, file_name=file_name)


def save_file(file_location: str, file_content: str | bytes, file_name: str) -> None:
    if os.name == 'nt':  # pragma: no cover
        # If the OS is Windows, replace colons with underscores (Windows does not support colons in file names).
        file_name = file_name.replace(':', '_')  # pragma: no cover
    if file_location.endswith('.zip'):
        with zf.ZipFile(file_location, 'a') as zip_file:
            zip_file.writestr(file_name, file_content)
    else:
        if not os.path.isdir(file_location):
            os.makedirs(file_location)
        file_path = os.path.join(file_location, file_name)
        save_type = 'wb' if type(file_content) is bytes else 'w'
        encoding: str | None = None if type(file_content) is bytes else 'utf-8'
        with open(file_path, save_type, encoding=encoding) as file:
            file.write(file_content)


class NonInstantiable:
    """Base classes of this class are only instantiable in the same module that they are defined in."""
    @classmethod
    def __init__(cls) -> None:
        caller_module_path = ins.stack()[2].filename
        class_module_path = ins.getfile(cls)
        # Ensure the python module of the caller matches that of the class
        # This ensures the class is only instantiated in the same module that it's defined in
        if caller_module_path != class_module_path:
            raise RuntimeError(f'The class "{cls.__name__}" cannot be instantiated outside of its module.')


class staticproperty(staticmethod):
    def __get__(self, *_) -> t.Any:
        return self.__func__()
