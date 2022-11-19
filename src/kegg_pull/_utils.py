import logging as l
import typing as t
import zipfile as zf
import os


def split_comma_separated_list(list_string: str) -> list:
    items: list = list_string.split(',')

    if '' in items:
        l.warning(f'Blank items detected in the comma separated list: "{list_string}". Removing blanks...')
        items = [item for item in items if item != '']

    # If the items end up being an empty list
    if not items:
        raise RuntimeError(f'ERROR - BAD INPUT: Empty list provided: "{list_string}"')

    return items


def get_molecular_attribute_args(args: dict) -> tuple:
    formula: str = args['--formula']
    exact_mass: list = args['--exact-mass']
    molecular_weight: list = args['--molecular-weight']

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


def handle_cli_output(output: str, output_content: t.Union[str, bytes]) -> None:
    if output is None:
        if type(output_content) is bytes:
            l.warning('Printing binary output...')

        print(output_content)
    else:
        if '.zip:' in output:
            [file_location, file_name] = output.split('.zip:')
            file_location: str = file_location + '.zip'
        else:
            file_location, file_name = os.path.split(output)
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
