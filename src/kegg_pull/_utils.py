import logging as l
import typing as t
import zipfile as zf
import os
import sys
import json as j
import jsonschema as js


def get_molecular_attribute_args(args: dict) -> tuple:
    formula: str = args['--formula']
    exact_mass: list = args['--em']
    molecular_weight: list = args['--mw']

    # exact_mass and molecular_weight will be [] (empty list) if not specified in the commandline args
    if exact_mass:
        exact_mass: t.Union[float, tuple] = _get_range_values(range_values=exact_mass, value_type=float)
    else:
        exact_mass = None

    if molecular_weight:
        molecular_weight: t.Union[int, tuple] = _get_range_values(range_values=molecular_weight, value_type=int)
    else:
        molecular_weight = None

    return formula, exact_mass, molecular_weight


def _get_range_values(range_values: t.Union[int, float, tuple], value_type: type) -> t.Union[int, float, tuple]:
    if len(range_values) == 1:
        [val] = range_values

        return value_type(val)
    elif len(range_values) == 2:
        [min_val, max_val] = range_values

        return value_type(min_val), value_type(max_val)
    else:
        raise ValueError(
            f'Range can only be specified by two values but {len(range_values)} values were provided: '
            f'{", ".join(str(range_value) for range_value in range_values)}'
        )


def load_json_file(file_path: str, json_schema: dict, validation_error_message: str) -> dict:
    if '.zip:' in file_path:
        [file_location, file_name] = file_path.split('.zip:')
        file_location: str = file_location + '.zip'

        with zf.ZipFile(file_location, 'r') as zip_file:
            json_object: bytes = zip_file.read(file_name)
            json_object: dict = j.loads(s=json_object)
    else:
        with open(file_path, 'r') as file:
            json_object: dict = j.load(file)

    validate_json_object(json_object=json_object, json_schema=json_schema, validation_error_message=validation_error_message)

    return json_object


def validate_json_object(json_object: dict, json_schema: dict, validation_error_message: str) -> None:
    try:
        js.validate(json_object, json_schema)
    except js.exceptions.ValidationError as e:
        l.error(validation_error_message)

        raise e


def parse_input_sequence(input_source: str) -> list:
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


def print_or_save(output_target: str, output_content: t.Union[str, bytes]) -> None:
    if output_target is None:
        if type(output_content) is bytes:
            l.warning('Printing binary output...')

        print(output_content)
    else:
        save_output(output_target=output_target, output_content=output_content)


def save_output(output_target: str, output_content: t.Union[str, bytes]) -> None:
    if '.zip:' in output_target:
        [file_location, file_name] = output_target.split('.zip:')
        file_location: str = file_location + '.zip'
    else:
        file_location, file_name = os.path.split(output_target)
        file_location = '.' if file_location == '' else file_location

    save_file(file_location=file_location, file_content=output_content, file_name=file_name)


def save_file(file_location: str, file_content: t.Union[str, bytes], file_name: str) -> None:
        if file_location.endswith('.zip'):
            with zf.ZipFile(file_location, 'a') as zip_file:
                zip_file.writestr(file_name, file_content)
        else:
            if not os.path.isdir(file_location):
                os.makedirs(file_location)

            file_path: str = os.path.join(file_location, file_name)
            save_type: str = 'wb' if type(file_content) is bytes else 'w'

            with open(file_path, save_type) as file:
                file.write(file_content)


class staticproperty(staticmethod):
    def __get__(self, *_):
        return self.__func__()
