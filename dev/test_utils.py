import pytest as pt
# noinspection PyProtectedMember
import kegg_pull._utils as utils
import dev.utils as u

@pt.mark.parametrize('comma_separated_list', [',,', ',', ''])
def test_handle_cli_input_comma_exception(comma_separated_list: str):
    with pt.raises(ValueError) as error:
        utils.handle_cli_input(input_source=comma_separated_list)

    expected_message = f'Empty list provided from comma separated list: "{comma_separated_list}"'
    u.assert_expected_error_message(expected_message=expected_message, error=error)


@pt.mark.parametrize('stdin_input', ['', '\n', '\t\t', '\n\n', '\t \n \t', ' \n \n\t\t \t\n'])
def test_handle_cli_input_stdin_exception(mocker, stdin_input: str):
    stdin_mock: mocker.MagicMock = mocker.patch('kegg_pull._utils.sys.stdin.read', return_value=stdin_input)

    with pt.raises(ValueError) as error:
        utils.handle_cli_input(input_source='-')

    stdin_mock.assert_called_once_with()
    expected_message = 'Empty list provided from standard input'
    u.assert_expected_error_message(expected_message=expected_message, error=error)


def test_get_range_values_exception():
    with pt.raises(ValueError) as error:
        utils._get_range_values(range_values=(1,2,3), value_type=int)

    expected_message = f'Range can only be specified by two values but 3 values were provided: 1, 2, 3'
    u.assert_expected_error_message(expected_message=expected_message, error=error)