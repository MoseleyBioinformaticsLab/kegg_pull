import pytest as pt
import kegg_pull._utils as utils
import tests.utils as u

def test_split_comma_separated_list_warning(caplog):
    comma_separated_list = 'a,,b'
    items: list = utils.split_comma_separated_list(list_string=comma_separated_list)
    warning = f'Blank items detected in the comma separated list: "{comma_separated_list}". Removing blanks...'
    u.assert_warning(message=warning, caplog=caplog)

    assert items == ['a', 'b']


def test_get_range_values_exception():
    with pt.raises(ValueError) as error:
        utils._get_range_values(range_values=(1,2,3), value_type=int)

    expected_message = f'Range can only be specified by two values but 3 values were provided: 1, 2, 3'
    u.assert_expected_error_message(expected_message=expected_message, error=error)