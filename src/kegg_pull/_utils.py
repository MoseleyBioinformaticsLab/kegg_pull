import logging as l
import typing as t


def split_comma_separated_list(list_string: str) -> list:
    items: list = list_string.split(',')

    if '' in items:
        l.warning(f'Blank items detected in the comma separated list: "{list_string}". Removing blanks...')
        items = [item for item in items if item != '']

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


class staticproperty(staticmethod):
    def __get__(self, *_):
        return self.__func__()
