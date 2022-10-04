import pytest as pt
import os
import typing as t
import json as j

import kegg_pull.pull_cli as p_cli
import dev.utils as u

testing_entry_ids = ['1', '2']


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=p_cli, subcommand='pull')


@pt.fixture(name='_')
def teardown():
    yield

    os.remove('pull-results.json')


test_main_single_data = [
    (
        ['--file-path=entry-ids.txt'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
        {'output_dir': '.', 'entry_field': None}
    ),
    (
        ['--entry-ids=1,2', '--output=out-dir/', '--sleep-time=10.1'],
        {'n_tries': None, 'time_out': None, 'sleep_time': 10.1}, {'output_dir': 'out-dir/', 'entry_field': None}
    ),
    (
        ['--entry-ids=1,2', '--n-tries=4', '--time-out=50', '--entry-field=mol'],
        {'n_tries': 4, 'time_out': 50, 'sleep_time': None}, {'output_dir': '.', 'entry_field': 'mol'}
    )
]
@pt.mark.parametrize('args,kegg_rest_kwargs,single_pull_kwargs', test_main_single_data)
def test_main_single(mocker, _, args: list, kegg_rest_kwargs: dict, single_pull_kwargs: dict):
    args = ['kegg_pull', 'pull', 'single'] + args

    if '--file-path=entry-ids.txt' in args:
        from_file_mock: mocker.MagicMock = mocker.patch(
            'kegg_pull.pull_cli.ei.EntryIdsGetter.from_file', return_value=testing_entry_ids
        )
    else:
        from_file_mock = None

    _test_pull(
        mocker=mocker, args=args, kegg_rest_kwargs=kegg_rest_kwargs, single_pull_kwargs=single_pull_kwargs
    )

    if from_file_mock is not None:
        from_file_mock.assert_called_once_with(file_path='entry-ids.txt')


def _test_pull(
    mocker, args: list, kegg_rest_kwargs: dict, single_pull_kwargs: dict, get_multiple_pull_mocks: t.Callable = None
):
    mocker.patch('sys.argv', args)
    kegg_rest_mock = mocker.MagicMock()
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)

    pull_result_mock = mocker.MagicMock(
        successful_entry_ids=('a', 'b', 'c', 'x'), failed_entry_ids=('y', 'z'), timed_out_entry_ids=()
    )

    single_pull_mock = mocker.MagicMock(pull=mocker.MagicMock(return_value=pull_result_mock))
    SinglePullMock = mocker.patch('kegg_pull.pull.SinglePull', return_value=single_pull_mock)

    if get_multiple_pull_mocks is not None:
        assert_multiple_pull_mocks: t.Callable = get_multiple_pull_mocks(single_pull_mock=single_pull_mock)
    else:
        assert_multiple_pull_mocks = None

    time_mock: mocker.MagicMock = mocker.patch('kegg_pull.pull_cli._testable_time', side_effect=[26, 94])
    p_cli.main()
    KEGGrestMock.assert_called_once_with(**kegg_rest_kwargs)
    SinglePullMock.assert_called_once_with(kegg_rest=kegg_rest_mock, **single_pull_kwargs)

    assert time_mock.call_count == 2

    if assert_multiple_pull_mocks is not None:
        assert_multiple_pull_mocks()
    else:
        single_pull_mock.pull.assert_called_once_with(entry_ids=testing_entry_ids)

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


test_main_multiple_data = [
    (
        ['--file-path=entry-ids.txt', '--entry-field=mol'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
        {'output_dir': '.', 'entry_field': 'mol'}, 'from_file', {'file_path': 'entry-ids.txt'},
        'SingleProcessMultiplePull', {'force_single_entry': False}
    ),
    (
        ['--database-name=pathway', '--output=out-dir', '--multi-process', '--sleep-time=20', '--force-single-entry'],
        {'n_tries': None, 'time_out': None, 'sleep_time': 20}, {'output_dir': 'out-dir', 'entry_field': None},
        'from_database', {'database_name': 'pathway'}, 'MultiProcessMultiplePull',
        {'force_single_entry': True, 'n_workers': None}
    ),
    (
        ['--database-name=brite', '--multi-process', '--n-tries=5', '--time-out=35', '--n-workers=6'],
        {'n_tries': 5, 'time_out': 35, 'sleep_time': None}, {'output_dir': '.', 'entry_field': None}, 'from_database',
        {'database_name': 'brite'}, 'MultiProcessMultiplePull', {'force_single_entry': True, 'n_workers': 6}
    )
]
@pt.mark.parametrize(
    'args,kegg_rest_kwargs,single_pull_kwargs,entry_ids_getter_method,entry_ids_getter_kwargs,multiple_pull_class,'
    'multiple_pull_kwargs', test_main_multiple_data
)
def test_main_multiple(
    mocker, _, args: list, kegg_rest_kwargs: dict, single_pull_kwargs: dict, entry_ids_getter_method: str,
    entry_ids_getter_kwargs: dict, multiple_pull_class: str, multiple_pull_kwargs: dict
):
    args = ['kegg_pull', 'pull', 'multiple'] + args

    def get_multiple_pull_mocks(single_pull_mock: mocker.MagicMock) -> t.Callable:
        entry_ids_getter_method_mock: mocker.MagicMock = mocker.patch(
            f'kegg_pull.pull_cli.ei.EntryIdsGetter.{entry_ids_getter_method}', return_value=testing_entry_ids
        )

        multiple_pull_mock = mocker.MagicMock(pull=single_pull_mock.pull)

        MultiplePullMock: mocker.MagicMock = mocker.patch(
            f'kegg_pull.pull.{multiple_pull_class}', return_value=multiple_pull_mock
        )

        def assert_multiple_pull_mocks():
            MultiplePullMock.assert_called_once_with(single_pull=single_pull_mock, **multiple_pull_kwargs)
            multiple_pull_mock.pull.assert_called_once_with(entry_ids=testing_entry_ids)
            entry_ids_getter_method_mock.assert_called_with(**entry_ids_getter_kwargs)

        return assert_multiple_pull_mocks

    _test_pull(
        mocker=mocker, args=args, kegg_rest_kwargs=kegg_rest_kwargs, single_pull_kwargs=single_pull_kwargs,
        get_multiple_pull_mocks=get_multiple_pull_mocks
    )
