# noinspection PyPackageRequirements
import pytest as pt
# noinspection PyProtectedMember
import kegg_pull._utils as utils
import dev.utils as u
import kegg_pull.pull as p
import kegg_pull.rest as r
import kegg_pull.pathway_organizer as po


@pt.mark.parametrize('comma_separated_list', [',,', ',', ''])
def test_parse_input_sequence_comma_exception(comma_separated_list: str):
    with pt.raises(ValueError) as error:
        utils.parse_input_sequence(input_source=comma_separated_list)
    expected_message = f'Empty list provided from comma separated list: "{comma_separated_list}"'
    u.assert_exception(expected_message=expected_message, exception=error)


@pt.mark.parametrize('stdin_input', ['', '\n', '\t\t', '\n\n', '\t \n \t', ' \n \n\t\t \t\n'])
def test_parse_input_sequence_stdin_exception(mocker, stdin_input: str):
    stdin_mock: mocker.MagicMock = mocker.patch('kegg_pull._utils.sys.stdin.read', return_value=stdin_input)
    with pt.raises(ValueError) as error:
        utils.parse_input_sequence(input_source='-')
    stdin_mock.assert_called_once_with()
    expected_message = 'Empty list provided from standard input'
    u.assert_exception(expected_message=expected_message, exception=error)


def test_get_range_values_exception():
    with pt.raises(ValueError) as error:
        utils._get_range_values(range_values=['1', '2', '3'], value_type=int)
    expected_message = f'Range can only be specified by two values but 3 values were provided: 1, 2, 3'
    u.assert_exception(expected_message=expected_message, exception=error)


@pt.mark.parametrize(
    'NonInstantiable,kwargs', [(p.PullResult, {}), (r.KEGGresponse, {'status': None, 'kegg_url': None}), (po.PathwayOrganizer, {})])
def test_non_instantiable(NonInstantiable: type, kwargs: dict):
    expected_error_message = f'The class "{NonInstantiable.__name__}" cannot be instantiated outside of its module.'
    with pt.raises(RuntimeError) as error:
        NonInstantiable(**kwargs)
    u.assert_exception(expected_message=expected_error_message, exception=error)
