# noinspection PyPackageRequirements
import pytest as pt
import shutil as sh
import os
import zipfile as zf
import itertools as i
import json
import kegg_pull.rest as r
import kegg_pull.pull as p
import dev.utils as u

testing_entry_ids = ['1', '2']


@pt.fixture(name='zip_file_path')
def remove_zip_file():
    zip_file_path = 'zip.zip'
    yield zip_file_path
    os.remove(zip_file_path)


def test_multiprocess_locking(mocker, zip_file_path: str):
    entry_ids_mock = ['xxx']
    expected_file_content = 'entry file content'
    kegg_response_mock = mocker.MagicMock(
        text_body=expected_file_content, kegg_url=mocker.MagicMock(multiple_entry_ids=False, entry_ids=entry_ids_mock),
        status=r.KEGGresponse.Status.SUCCESS)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.pull.r.KEGGrest.get', return_value=kegg_response_mock)
    lock_mock = mocker.MagicMock(acquire=mocker.MagicMock(), release=mocker.MagicMock())
    LockMock: mocker.MagicMock = mocker.patch('kegg_pull.pull.mp.Lock', return_value=lock_mock)
    single_pull = p.SinglePull()
    pull_result: p.PullResult = single_pull.pull(entry_ids=entry_ids_mock, output=zip_file_path, multiprocess_lock_save=True)
    assert single_pull._multiprocess_lock == lock_mock
    LockMock.assert_called_once_with()
    get_mock.assert_called_once_with(entry_ids=entry_ids_mock, entry_field=None)
    lock_mock.acquire.assert_called_once_with()
    lock_mock.release.assert_called_once_with()
    with zf.ZipFile(zip_file_path, 'r') as zip_file:
        actual_file_content: str = zip_file.read(f'xxx.txt').decode()
    assert actual_file_content == expected_file_content
    assert str(pull_result) == 'Successful Entry Ids: xxx\nFailed Entry Ids: none\nTimed Out Entry Ids: none'


@pt.fixture(name='output_mock', params=['mock-dir/', 'mock.zip', None])
def setup_and_teardown(request):
    # Setup
    output_mock = request.param
    yield output_mock
    # Tear down
    if output_mock is not None:
        if output_mock.endswith('.zip') and os.path.isfile(output_mock):
            os.remove(output_mock)
        else:
            sh.rmtree(output_mock, ignore_errors=True)


test_separate_entries_data = [(None, '///'), ('mol', '$$$$'), ('kcf', '///'), ('aaseq', '>'), ('ntseq', '>')]


@pt.mark.parametrize('entry_field,separator', test_separate_entries_data)
def test_separate_entries(mocker, output_mock: str, entry_field: str, separator: str):
    entry_ids_mock = ['abc', 'xyz', '123']
    expected_entries = [f'{entry_id_mock} content' for entry_id_mock in entry_ids_mock]
    if entry_field == 'aaseq' or entry_field == 'ntseq':
        text_body_mock = separator + separator.join(expected_entries)
    else:
        text_body_mock = separator.join(expected_entries) + separator
    response_mock = mocker.MagicMock(
        text_body=text_body_mock, status=r.KEGGresponse.Status.SUCCESS,
        kegg_url=mocker.MagicMock(multiple_entry_ids=True, entry_ids=entry_ids_mock))
    kegg_rest_mock = mocker.MagicMock(get=mocker.MagicMock(return_value=response_mock))
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)
    single_pull = p.SinglePull()
    KEGGrestMock.assert_called_once_with()
    kegg_entry_mapping: p.KEGGentryMapping | None = None
    if output_mock is not None:
        pull_result: p.PullResult = single_pull.pull(entry_ids=entry_ids_mock, output=output_mock, entry_field=entry_field)
    else:
        pull_result, kegg_entry_mapping = single_pull.pull_dict(entry_ids=entry_ids_mock, entry_field=entry_field)
    kegg_rest_mock.get.assert_called_once_with(entry_ids=entry_ids_mock, entry_field=entry_field)
    assert pull_result.successful_entry_ids == tuple(entry_ids_mock)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()
    if kegg_entry_mapping:
        for entry_id_mock, expected_entry in zip(entry_ids_mock, expected_entries):
            assert kegg_entry_mapping[entry_id_mock] == expected_entry
    else:
        for entry_id_mock, expected_file_content in zip(entry_ids_mock, expected_entries):
            expected_file_extension = 'txt' if entry_field is None else entry_field
            expected_file = f'{entry_id_mock}.{expected_file_extension}'
            if output_mock.endswith('.zip'):
                with zf.ZipFile(output_mock, 'r') as zip_file:
                    actual_file_content: str = zip_file.read(name=expected_file).decode()
            else:
                expected_file: str = os.path.join(output_mock, expected_file)
                with open(expected_file, 'r') as file:
                    actual_file_content: str = file.read()
            assert actual_file_content == expected_file_content


@pt.fixture(name='output_dir', params=['out-dir/', None])
def make_and_remove_output_dir(request):
    output_dir = request.param
    if output_dir is not None:
        os.mkdir(output_dir)
    yield output_dir
    if output_dir is not None:
        sh.rmtree(output_dir)


def test_pull_separate_entries(mocker, output_dir: str):
    success_entry_id = 'success-entry-id'
    failed_entry_id = 'fail-entry-id'
    time_out_entry_id = 'time-out-entry-id'
    entry_ids_mock = [failed_entry_id, success_entry_id, time_out_entry_id]
    get_url_mock = mocker.MagicMock(multiple_entry_ids=True, entry_ids=entry_ids_mock)
    initial_response_mock = mocker.MagicMock(status=r.KEGGresponse.Status.FAILED, kegg_url=get_url_mock)
    entry_response_mock1 = mocker.MagicMock(status=r.KEGGresponse.Status.FAILED)
    expected_entry = 'successful entry'
    entry_response_mock2 = mocker.MagicMock(
        text_body=expected_entry, status=r.KEGGresponse.Status.SUCCESS, kegg_url=mocker.MagicMock(entry_ids=[success_entry_id]))
    entry_response_mock3 = mocker.MagicMock(status=r.KEGGresponse.Status.TIMEOUT)
    get_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.pull.r.KEGGrest.get',
        side_effect=[initial_response_mock, entry_response_mock1, entry_response_mock2, entry_response_mock3])
    single_pull = p.SinglePull()
    kegg_entry_mapping: p.KEGGentryMapping | None = None
    if output_dir is not None:
        pull_result: p.PullResult = single_pull.pull(entry_ids=entry_ids_mock, output=output_dir)
    else:
        pull_result, kegg_entry_mapping = single_pull.pull_dict(entry_ids=entry_ids_mock)
    expected_get_call_kwargs = [
        {'entry_ids': entry_ids_mock, 'entry_field': None}, {'entry_ids': [failed_entry_id], 'entry_field': None},
        {'entry_ids': [success_entry_id], 'entry_field': None}, {'entry_ids': [time_out_entry_id], 'entry_field': None}]
    u.assert_call_args(function_mock=get_mock, expected_call_args_list=expected_get_call_kwargs, do_kwargs=True)
    assert pull_result.successful_entry_ids == (success_entry_id,)
    assert pull_result.failed_entry_ids == (failed_entry_id,)
    assert pull_result.timed_out_entry_ids == (time_out_entry_id,)
    assert str(pull_result) == f'Successful Entry Ids: {success_entry_id}\n'\
                               f'Failed Entry Ids: {failed_entry_id}\n'\
                               f'Timed Out Entry Ids: {time_out_entry_id}'
    if kegg_entry_mapping:
        assert kegg_entry_mapping[success_entry_id] == expected_entry
    else:
        with open(f'{output_dir}/{success_entry_id}.txt') as file:
            actual_file_content: str = file.read()
        assert actual_file_content == expected_entry


@pt.fixture(name='file_name', params=['single-entry-id.image', None])
def remove_file(request):
    file_name = request.param
    yield file_name
    if file_name is not None and os.path.isfile(file_name):
        os.remove(file_name)


@pt.mark.parametrize('status', [r.KEGGresponse.Status.SUCCESS, r.KEGGresponse.Status.FAILED])
def test_single_entry(mocker, file_name: str, status: r.KEGGresponse.Status):
    single_entry_id = 'single-entry-id'
    binary_body_mock = b'binary body mock'
    kegg_response_mock = mocker.MagicMock(
        kegg_url=mocker.MagicMock(entry_ids=[single_entry_id], multiple_entry_ids=False), binary_body=binary_body_mock, status=status)
    mocker.patch('kegg_pull.rest.KEGGrest.get', return_value=kegg_response_mock)
    single_pull = p.SinglePull()
    kegg_entry_mapping: p.KEGGentryMapping | None = None
    if file_name is not None:
        pull_result: p.PullResult = single_pull.pull(entry_ids=[single_entry_id], output='.', entry_field='image')
    else:
        pull_result, kegg_entry_mapping = single_pull.pull_dict(entry_ids=[single_entry_id], entry_field='image')
    assert pull_result.timed_out_entry_ids == ()
    if status == r.KEGGresponse.Status.SUCCESS:
        assert pull_result.successful_entry_ids == (single_entry_id,)
        assert pull_result.failed_entry_ids == ()
        if kegg_entry_mapping:
            assert kegg_entry_mapping[single_entry_id] == binary_body_mock
        else:
            with open(file_name, 'rb') as file:
                actual_file_content: bytes = file.read()
            assert actual_file_content == binary_body_mock
    else:
        assert pull_result.successful_entry_ids == ()
        assert pull_result.failed_entry_ids == (single_entry_id,)


@pt.fixture(name='entry_field', params=['mol', 'ntseq'])
def remove_entries(request):
    entry_field = request.param
    yield entry_field
    os.remove(f'entry-id1.{entry_field}')
    os.remove(f'entry-id2.{entry_field}')


def test_not_all_requested_entries(mocker, entry_field: str):
    entry_id1 = 'entry-id1'
    entry_id2 = 'entry-id2'
    separate_text_body1 = 'separate text body 1'
    separate_text_body2 = 'separate text body 2'
    initial_kegg_response_mock = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body=separate_text_body1, kegg_url=mocker.MagicMock(entry_ids=[entry_id1, entry_id2]))
    separate_response_mock1 = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body=separate_text_body1,
        kegg_url=mocker.MagicMock(entry_ids=[entry_id1]))
    separate_response_mock2 = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body=separate_text_body2, kegg_url=mocker.MagicMock(entry_ids=[entry_id2]))
    get_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.pull.r.KEGGrest.get', side_effect=[separate_response_mock1, separate_response_mock2])
    u.mock_non_instantiable(mocker=mocker)
    pull_result = p.PullResult()
    single_pull = p.SinglePull()
    single_pull._entry_field = entry_field
    single_pull._output = '.'
    single_pull._save_multi_entry_response(kegg_response=initial_kegg_response_mock, pull_result=pull_result)
    assert pull_result.successful_entry_ids == (entry_id1, entry_id2)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()
    expected_get_call_kwargs = [
        {'entry_ids': [entry_id1], 'entry_field': entry_field}, {'entry_ids': [entry_id2], 'entry_field': entry_field}]
    u.assert_call_args(function_mock=get_mock, expected_call_args_list=expected_get_call_kwargs, do_kwargs=True)
    for entry_id, expected_file_content in zip([entry_id1, entry_id2], [separate_text_body1, separate_text_body2]):
        file_name = f'{entry_id}.{entry_field}'
        with open(file_name, 'r') as file:
            actual_file_content: str = file.read()
        assert actual_file_content == expected_file_content


@pt.fixture(name='multiple_pull_output', params=['x', None])
def get_multiple_pull_output(request):
    output = request.param
    yield output


@pt.fixture(name='_')
def remove_aborted_pull_results():
    yield
    if os.path.isfile(p.AbstractMultiplePull.ABORTED_PULL_RESULTS_PATH):
        os.remove(p.AbstractMultiplePull.ABORTED_PULL_RESULTS_PATH)


test_multiple_pull_data = [
    (p.SingleProcessMultiplePull, {}), (p.MultiProcessMultiplePull, {'n_workers': 2}),
    (p.MultiProcessMultiplePull, {'n_workers': None}), (p.MultiProcessMultiplePull, {'unsuccessful_threshold': 0.01})]


@pt.mark.parametrize('MultiplePull,kwargs', test_multiple_pull_data)
def test_multiple_pull(
        mocker, MultiplePull: type[p.MultiProcessMultiplePull | p.SingleProcessMultiplePull], kwargs: dict,
        multiple_pull_output: str | None, caplog, _):
    expected_pull_calls = [
        ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'], ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],
        ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], ['D0', 'D1']]
    entry_ids_mock = list(i.chain.from_iterable(expected_pull_calls))
    single_pull_mock = PickleableSinglePullMock()
    SinglePullMock = mocker.patch('kegg_pull.pull.SinglePull', return_value=single_pull_mock)
    if MultiplePull is p.SingleProcessMultiplePull:
        single_pull_mock.pull = mocker.spy(single_pull_mock, 'pull')
        single_pull_mock.pull_dict = mocker.spy(single_pull_mock, 'pull_dict')
    kegg_rest_mock = mocker.MagicMock()
    multiple_pull = MultiplePull(kegg_rest=kegg_rest_mock, **kwargs)
    SinglePullMock.assert_called_once_with(kegg_rest=kegg_rest_mock)
    if 'unsuccessful_threshold' in kwargs:
        with pt.raises(SystemExit) as error:
            if multiple_pull_output:
                multiple_pull.pull(entry_ids=entry_ids_mock, output=multiple_pull_output)
            else:
                multiple_pull.pull_dict(entry_ids=entry_ids_mock)
        error_message = f'Unsuccessful threshold of {kwargs["unsuccessful_threshold"]} met. Aborting. ' \
                        f'Details saved at {p.AbstractMultiplePull.ABORTED_PULL_RESULTS_PATH}'
        u.assert_error(message=error_message, caplog=caplog)
        assert error.value.args == (1,)
        expected_abort_results = {
            'num-remaining-entry-ids': 22, 'num-successful': 9, 'num-failed': 1, 'num-timed-out': 0,
            'remaining-entry-ids': [
                'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
                'C7', 'C8', 'C9', 'D0', 'D1'],
            'successful-entry-ids': ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8'], 'failed-entry-ids': ['A9'],
            'timed-out-entry-ids': []}
        with open(p.AbstractMultiplePull.ABORTED_PULL_RESULTS_PATH, 'r') as file:
            actual_abort_results: dict = json.load(file)
        assert expected_abort_results == actual_abort_results
    else:
        kegg_entry_mapping: p.KEGGentryMapping | None = None
        if multiple_pull_output:
            multiple_pull_result = multiple_pull.pull(entry_ids=entry_ids_mock, output=multiple_pull_output)
        else:
            multiple_pull_result, kegg_entry_mapping = multiple_pull.pull_dict(entry_ids=entry_ids_mock)
        expected_successful_entry_ids = (
            'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
            'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'D0')
        expected_failed_entry_ids = ('A9', 'B9', 'C9', 'D1')
        expected_timed_out_entry_ids = ()
        assert multiple_pull_result.successful_entry_ids == expected_successful_entry_ids
        assert multiple_pull_result.failed_entry_ids == expected_failed_entry_ids
        assert multiple_pull_result.timed_out_entry_ids == expected_timed_out_entry_ids
        if MultiplePull is p.SingleProcessMultiplePull:
            expected_call_args_list = [
                {'entry_ids': expected_pull_call, 'entry_field': None} for expected_pull_call in expected_pull_calls]
            if multiple_pull_output:
                for expected_call_args in expected_call_args_list:
                    expected_call_args['output'] = multiple_pull_output
                u.assert_call_args(function_mock=single_pull_mock.pull, expected_call_args_list=expected_call_args_list, do_kwargs=True)
            else:
                u.assert_call_args(function_mock=single_pull_mock.pull_dict, expected_call_args_list=expected_call_args_list, do_kwargs=True)
                assert sorted(expected_successful_entry_ids) == sorted(kegg_entry_mapping.keys())
                for entry_id in expected_successful_entry_ids:
                    assert kegg_entry_mapping[entry_id] == f'{entry_id} - content'


class PickleableSinglePullMock:
    """
    Since the multiprocessing module cannot pickle the MagicMock class built into pytest, and since Windows has to pickle even
    global variables going into the child processes via the "initargs", we need to create this dummy class to replace MagicMock.
    see https://stackoverflow.com/questions/43457569/multiprocessing-pool-initializer-fails-pickling
    and https://stackoverflow.com/questions/9670926/multiprocessing-on-windows-breaks
    """
    class PickleablePullResultMock:
        """
        A regular PullResult object will raise an exception if instantiated outside the pull module, and we cannot take advantage of
        the "mock_non_instantiable" function in dev/utils.py since Windows cannot handle that either.
        """
        def __init__(self, successful_entry_ids: tuple, failed_entry_ids: tuple):
            self.successful_entry_ids = successful_entry_ids
            self.failed_entry_ids = failed_entry_ids
            self.timed_out_entry_ids = ()

    @staticmethod
    def pull(entry_ids: list, **_) -> PickleablePullResultMock:
        successful_entry_ids = tuple(entry_ids[:-1])
        failed_entry_ids = tuple(entry_ids[-1:])
        single_pull_result = PickleableSinglePullMock.PickleablePullResultMock(
            successful_entry_ids=successful_entry_ids, failed_entry_ids=failed_entry_ids)
        return single_pull_result

    @staticmethod
    def pull_dict(entry_ids: list, **_) -> tuple[PickleablePullResultMock, p.KEGGentryMapping]:
        single_pull_result = PickleableSinglePullMock.pull(entry_ids=entry_ids)
        return single_pull_result, {entry_id: f'{entry_id} - content' for entry_id in single_pull_result.successful_entry_ids}


@pt.mark.parametrize('MultiplePull,kwargs', test_multiple_pull_data)
def test_get_n_entries_per_url(mocker, MultiplePull: type, kwargs: dict):
    entry_ids_mock = ['eid1', 'eid2', 'eid3', 'eid4']
    SinglePullMock = mocker.patch('kegg_pull.pull.SinglePull', return_value=PickleableSinglePullMock())
    multiple_pull = MultiplePull(kegg_rest=None, **kwargs)
    SinglePullMock.assert_called_once_with(kegg_rest=None)
    group_entry_ids_spy: mocker.MagicMock = mocker.spy(multiple_pull, '_group_entry_ids')
    get_n_entries_per_url_spy: mocker.MagicMock = mocker.spy(p.AbstractMultiplePull, '_get_n_entries_per_url')
    pull_mock = mocker.patch(f'kegg_pull.pull.{MultiplePull.__name__}._concrete_pull')
    multiple_pull.pull(entry_ids=entry_ids_mock, output='x.zip', force_single_entry=True, entry_field='compound')
    group_entry_ids_spy.assert_called_once_with(entry_ids_to_group=entry_ids_mock)
    get_n_entries_per_url_spy.assert_called_once_with(multiple_pull)
    expected_grouped_entry_ids = [[entry_id] for entry_id in entry_ids_mock]
    pull_mock.assert_called_once()
    assert group_entry_ids_spy.spy_return == expected_grouped_entry_ids
    assert get_n_entries_per_url_spy.spy_return == 1
    group_entry_ids_spy.reset_mock()
    get_n_entries_per_url_spy.reset_mock()
    pull_mock.reset_mock()
    multiple_pull.pull(entry_ids=entry_ids_mock, output='x.zip', entry_field='json')
    group_entry_ids_spy.assert_called_once_with(entry_ids_to_group=entry_ids_mock)
    get_n_entries_per_url_spy.assert_called_once_with(multiple_pull)
    pull_mock.assert_called_once()
    assert group_entry_ids_spy.spy_return == expected_grouped_entry_ids
    assert get_n_entries_per_url_spy.spy_return == 1


test_get_single_pull_result_data = ['entry-field-mock', None]


@pt.mark.parametrize('entry_field_mock', test_get_single_pull_result_data)
def test_get_single_pull_result(mocker, output_mock: str | None, entry_field_mock: str | None):
    u.mock_non_instantiable(mocker=mocker)
    return_value = 'return value'
    single_pull_mock = mocker.MagicMock(
        pull=mocker.MagicMock(return_value=return_value), pull_dict=mocker.MagicMock(return_value=return_value))
    mocker.patch('kegg_pull.pull._global_single_pull', single_pull_mock)
    mocker.patch('kegg_pull.pull._global_output', output_mock)
    mocker.patch('kegg_pull.pull._global_entry_field', entry_field_mock)
    actual_result: bytes = p._get_single_pull_result(entry_ids=testing_entry_ids)
    if output_mock:
        single_pull_mock.pull.assert_called_once_with(
            entry_ids=testing_entry_ids, output=output_mock, entry_field=entry_field_mock,
            multiprocess_lock_save=True)
    else:
        single_pull_mock.pull_dict.assert_called_once_with(entry_ids=testing_entry_ids, entry_field=entry_field_mock)
    assert actual_result == p.p.dumps(return_value)


@pt.mark.parametrize('unsuccessful_threshold', [1.2, -2.0])
def test_multiple_pull_exception(unsuccessful_threshold):
    expected_message = f'Unsuccessful threshold of {unsuccessful_threshold} is out of range. Valid values are within ' \
                       f'0.0 and 1.0, non-inclusive'
    with pt.raises(ValueError) as error:
        p.SingleProcessMultiplePull(kegg_rest=None, unsuccessful_threshold=unsuccessful_threshold)
    u.assert_exception(expected_message=expected_message, exception=error)
