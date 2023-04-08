# noinspection PyPackageRequirements
import pytest as pt
import os
import json
import kegg_pull.pull_cli as p_cli
import dev.utils as u


def test_help(mocker):
    u.assert_help(mocker=mocker, module=p_cli, subcommand='pull')


@pt.fixture(name='_')
def teardown():
    yield
    os.remove('pull-results.json')


test_data = [
    (['database', 'db-mock', '--print'], {'n_tries': None, 'time_out': None, 'sleep_time': None}, 'ei.from_database',
     {'database': 'db-mock'}, 'SingleProcessMultiplePull', {'unsuccessful_threshold': None},
     {'force_single_entry': False, 'entry_field': None}, True, None),
    (['database', 'db-mock', '--print', '--sep=#####', '--force-single-entry', '--ut=0.1', '--multi-process', '--entry-field=image'],
     {'n_tries': None, 'time_out': None, 'sleep_time': None}, 'ei.from_database', {'database': 'db-mock'}, 'MultiProcessMultiplePull',
     {'unsuccessful_threshold': 0.1, 'n_workers': None}, {'force_single_entry': True, 'entry_field': 'image'}, True, '#####'),
    (['entry-ids', '-'], {'n_tries': None, 'time_out': None, 'sleep_time': None}, 'u.parse_input_sequence', {'input_source': '-'},
     'SingleProcessMultiplePull', {'unsuccessful_threshold': None}, {'output': '.', 'force_single_entry': False, 'entry_field': None},
     False, None),
    (['entry-ids', '1,2', '--output=out-dir/', '--sleep-time=10.1'], {'n_tries': None, 'time_out': None, 'sleep_time': 10.1},
     'u.parse_input_sequence', {'input_source': '1,2'}, 'SingleProcessMultiplePull', {'unsuccessful_threshold': None},
     {'output': 'out-dir/', 'force_single_entry': False, 'entry_field': None}, False, None),
    (['entry-ids', '1,2', '--n-tries=4', '--time-out=50', '--entry-field=mol'], {'n_tries': 4, 'time_out': 50, 'sleep_time': None},
     'u.parse_input_sequence', {'input_source': '1,2'}, 'SingleProcessMultiplePull', {'unsuccessful_threshold': None},
     {'output': '.', 'force_single_entry': False, 'entry_field': 'mol'}, False, None),
    (['entry-ids', '-', '--entry-field=mol'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
     'u.parse_input_sequence', {'input_source': '-'}, 'SingleProcessMultiplePull', {'unsuccessful_threshold': None},
     {'output': '.', 'force_single_entry': False, 'entry_field': 'mol'}, False, None),
    (['database', 'pathway', '--output=out-dir', '--multi-process', '--sleep-time=20', '--force-single-entry'],
     {'n_tries': None, 'time_out': None, 'sleep_time': 20}, 'ei.from_database', {'database': 'pathway'}, 'MultiProcessMultiplePull',
     {'n_workers': None, 'unsuccessful_threshold': None}, {'output': 'out-dir', 'force_single_entry': True, 'entry_field': None}, False,
     None),
    (['database', 'brite', '--multi-process', '--n-tries=5', '--time-out=35', '--n-workers=6'],
     {'n_tries': 5, 'time_out': 35, 'sleep_time': None}, 'ei.from_database', {'database': 'brite'}, 'MultiProcessMultiplePull',
     {'n_workers': 6, 'unsuccessful_threshold': None}, {'output': '.', 'force_single_entry': True, 'entry_field': None}, False, None),
    (['entry-ids', '-', '--ut=0.4'], {'n_tries': None, 'time_out': None, 'sleep_time': None},
     'u.parse_input_sequence', {'input_source': '-'}, 'SingleProcessMultiplePull', {'unsuccessful_threshold': 0.4},
     {'output': '.', 'force_single_entry': False, 'entry_field': None}, False, None)]


@pt.mark.parametrize(
    'args,kegg_rest_kwargs,entry_ids_method,entry_ids_kwargs,multiple_pull_class,multiple_pull_kwargs,pull_kwargs,print_to_screen,separator',
    test_data)
def test_main(
        mocker, _, args: list, kegg_rest_kwargs: dict, entry_ids_method: str, entry_ids_kwargs: dict, multiple_pull_class: str,
        multiple_pull_kwargs: dict, pull_kwargs: dict, print_to_screen: bool, separator: str | None, caplog):
    args = ['kegg_pull', 'pull'] + args
    mocker.patch('sys.argv', args)
    kegg_rest_mock = mocker.MagicMock()
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)
    pull_result_mock = mocker.MagicMock(
        successful_entry_ids=('a', 'b', 'c', 'x'), failed_entry_ids=('y', 'z'), timed_out_entry_ids=())
    pull_dict_return_value = pull_result_mock, {'a': 'x', 'b': 'y', 'c': 'z', 'x': 'abc123'}
    entry_ids_mock = ['1', '2']
    entry_ids_method_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.pull_cli.{entry_ids_method}', return_value=entry_ids_mock)
    multiple_pull_mock = mocker.MagicMock(
        pull=mocker.MagicMock(return_value=pull_result_mock),
        pull_dict=mocker.MagicMock(return_value=pull_dict_return_value))
    MultiplePullMock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.pull_cli.p.{multiple_pull_class}', return_value=multiple_pull_mock)
    time_mock: mocker.MagicMock = mocker.patch('kegg_pull.pull_cli._testable_time', side_effect=[26, 94])
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    p_cli.main()
    KEGGrestMock.assert_called_once_with(**kegg_rest_kwargs)
    assert time_mock.call_count == 2
    MultiplePullMock.assert_called_once_with(kegg_rest=kegg_rest_mock, **multiple_pull_kwargs)
    if print_to_screen:
        multiple_pull_mock.pull_dict.assert_called_once_with(entry_ids=entry_ids_mock, **pull_kwargs)
        if pull_kwargs['entry_field'] is not None:
            u.assert_warning(message='Printing binary output...', caplog=caplog)
        if separator is not None:
            print_mock.assert_called_once_with(f'\n{separator}\n'.join(['x', 'y', 'z', 'abc123']))
        else:
            u.assert_call_args(
                function_mock=print_mock, expected_call_args_list=[(arg,) for arg in ['a', 'x\n', 'b', 'y\n', 'c', 'z\n', 'x', 'abc123\n']],
                do_kwargs=False)
    else:
        multiple_pull_mock.pull.assert_called_once_with(entry_ids=entry_ids_mock, **pull_kwargs)
    entry_ids_method_mock.assert_called_with(**entry_ids_kwargs)
    expected_pull_results = {
        'percent-success': 66.67, 'pull-minutes': 1.13, 'num-successful': 4, 'num-failed': 2, 'num-timed-out': 0, 'num-total': 6,
        'successful-entry-ids': ['a', 'b', 'c', 'x'], 'failed-entry-ids': ['y', 'z'], 'timed-out-entry-ids': []}
    with open('pull-results.json', 'r') as file:
        actual_pull_results: dict = json.load(file)
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
        '}'])
    with open('pull-results.json', 'r') as file:
        actual_pull_results_text: str = file.read()
    assert expected_pull_results_text == actual_pull_results_text
