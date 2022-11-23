import pytest as pt
import os
import json as j

import kegg_pull.pull_cli as p_cli
import dev.utils as u


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=p_cli, subcommand='pull')


@pt.fixture(name='_')
def teardown():
    yield

    os.remove('pull-results.json')


test_main_data = [
    (
        ['entry-ids', '-'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
        {'output': '.', 'entry_field': None, 'multiprocess_lock_save': False}, 'u.handle_cli_input', {'input_source': '-'},
        'SingleProcessMultiplePull', {'force_single_entry': False, 'unsuccessful_threshold': None}
    ),
    (
        ['entry-ids', '1,2', '--output=out-dir/', '--sleep-time=10.1'], {'n_tries': None, 'time_out': None, 'sleep_time': 10.1},
        {'output': 'out-dir/', 'entry_field': None, 'multiprocess_lock_save': False}, 'u.handle_cli_input', {'input_source': '1,2'},
        'SingleProcessMultiplePull', {'force_single_entry': False, 'unsuccessful_threshold': None}
    ),
    (
        ['entry-ids', '1,2', '--n-tries=4', '--time-out=50', '--entry-field=mol'], {'n_tries': 4, 'time_out': 50, 'sleep_time': None},
        {'output': '.', 'entry_field': 'mol', 'multiprocess_lock_save': False}, 'u.handle_cli_input', {'input_source': '1,2'},
        'SingleProcessMultiplePull', {'force_single_entry': False, 'unsuccessful_threshold': None}
    ),
    (
        ['entry-ids', '-', '--entry-field=mol'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
        {'output': '.', 'entry_field': 'mol', 'multiprocess_lock_save': False}, 'u.handle_cli_input', {'input_source': '-'},
        'SingleProcessMultiplePull', {'force_single_entry': False, 'unsuccessful_threshold': None}
    ),
    (
        ['database', 'pathway', '--output=out-dir', '--multi-process', '--sleep-time=20', '--force-single-entry'],
        {'n_tries': None, 'time_out': None, 'sleep_time': 20},
        {'output': 'out-dir', 'entry_field': None, 'multiprocess_lock_save': False}, 'ei.from_database', {'database_name': 'pathway'},
        'MultiProcessMultiplePull', {'force_single_entry': True, 'n_workers': None, 'unsuccessful_threshold': None}
    ),
    (
        ['database', 'brite', '--multi-process', '--n-tries=5', '--time-out=35', '--n-workers=6'],
        {'n_tries': 5, 'time_out': 35, 'sleep_time': None}, {'output': '.', 'entry_field': None, 'multiprocess_lock_save': False},
        'ei.from_database', {'database_name': 'brite'}, 'MultiProcessMultiplePull',
        {'force_single_entry': True, 'n_workers': 6, 'unsuccessful_threshold': None}
    ),
    (
        ['entry-ids', '-', '--ut=0.4'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
        {'output': '.', 'entry_field': None, 'multiprocess_lock_save': False}, 'u.handle_cli_input', {'input_source': '-'},
        'SingleProcessMultiplePull', {'force_single_entry': False, 'unsuccessful_threshold': 0.4}
    )
]
@pt.mark.parametrize(
    'args,kegg_rest_kwargs,single_pull_kwargs,entry_ids_method,entry_ids_kwargs,multiple_pull_class,'
    'multiple_pull_kwargs', test_main_data
)
def test_main(
    mocker, _, args: list, kegg_rest_kwargs: dict, single_pull_kwargs: dict, entry_ids_method: str,
    entry_ids_kwargs: dict, multiple_pull_class: str, multiple_pull_kwargs: dict
):
    args = ['kegg_pull', 'pull'] + args
    mocker.patch('sys.argv', args)
    kegg_rest_mock = mocker.MagicMock()
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)

    pull_result_mock = mocker.MagicMock(
        successful_entry_ids=('a', 'b', 'c', 'x'), failed_entry_ids=('y', 'z'), timed_out_entry_ids=()
    )

    single_pull_mock = mocker.MagicMock(pull=mocker.MagicMock(return_value=pull_result_mock))
    SinglePullMock = mocker.patch('kegg_pull.pull_cli.p.SinglePull', return_value=single_pull_mock)
    entry_ids_mock = ['1', '2']

    entry_ids_method_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.pull_cli.{entry_ids_method}', return_value=entry_ids_mock
    )

    multiple_pull_mock = mocker.MagicMock(pull=single_pull_mock.pull)

    MultiplePullMock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.pull_cli.p.{multiple_pull_class}', return_value=multiple_pull_mock
    )

    time_mock: mocker.MagicMock = mocker.patch('kegg_pull.pull_cli._testable_time', side_effect=[26, 94])
    p_cli.main()
    KEGGrestMock.assert_called_once_with(**kegg_rest_kwargs)
    SinglePullMock.assert_called_once_with(kegg_rest=kegg_rest_mock, **single_pull_kwargs)

    assert time_mock.call_count == 2

    MultiplePullMock.assert_called_once_with(single_pull=single_pull_mock, **multiple_pull_kwargs)
    multiple_pull_mock.pull.assert_called_once_with(entry_ids=entry_ids_mock)
    entry_ids_method_mock.assert_called_with(**entry_ids_kwargs)

    expected_pull_results = {
        'percent-success': 66.67,
        'pull-minutes': 1.13,
        'num-successful': 4,
        'num-failed': 2,
        'num-timed-out': 0,
        'num-total': 6,
        'successful-entry-ids': ['a', 'b', 'c', 'x'],
        'failed-entry-ids': ['y', 'z'],
        'timed-out-entry-ids': []
    }

    with open('pull-results.json', 'r') as file:
        actual_pull_results: dict = j.load(file)

    assert actual_pull_results == expected_pull_results

    expected_pull_results_text: str = '\n'.join([
        '{',
        '"percent-success": 66.67,',
        '"pull-minutes": 1.13,',
        '"num-successful": 4,',
        '"num-failed": 2,',
        '"num-timed-out": 0,',
        '"num-total": 6,',
        '"successful-entry-ids": [',
        '"a",',
        '"b",',
        '"c",',
        '"x"',
        '],',
        '"failed-entry-ids": [',
        '"y",',
        '"z"',
        '],',
        '"timed-out-entry-ids": []',
        '}'
    ])

    with open('pull-results.json', 'r') as file:
        actual_pull_results_text: str = file.read()

    assert expected_pull_results_text == actual_pull_results_text
