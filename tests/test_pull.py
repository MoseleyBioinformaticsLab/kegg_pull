import pytest as pt
import shutil as sh
import os
import zipfile as zf
import itertools as i

import kegg_pull.rest as r
import kegg_pull.pull as p
import tests.utils as u


@pt.fixture(name='output_dir_mock', params=['mock-dir/', 'mock.zip'])
def setup_and_teardown(request):
    # Setup
    output_dir_mock = request.param

    yield output_dir_mock

    # Tear down
    if output_dir_mock.endswith('.zip') and os.path.isfile(output_dir_mock):
        os.remove(output_dir_mock)
    else:
        sh.rmtree(output_dir_mock, ignore_errors=True)


test_separate_entries_data = [
    (None, '///'), ('mol', '$$$$'), ('kcf', '///'), ('aaseq', '>'), ('ntseq', '>')
]
@pt.mark.parametrize('entry_field,separator', test_separate_entries_data)
def test_separate_entries(mocker, output_dir_mock: str, entry_field: str, separator: str):
    entry_ids_mock = ['abc', 'xyz', '123']
    expected_file_contents = [f'{entry_id_mock} content' for entry_id_mock in entry_ids_mock]

    if entry_field == 'aaseq' or entry_field == 'ntseq':
        text_body_mock = separator + separator.join(expected_file_contents)
    else:
        text_body_mock = separator.join(expected_file_contents) + separator

    response_mock = mocker.MagicMock(
        text_body=text_body_mock, status=r.KEGGresponse.Status.SUCCESS,
        kegg_url=mocker.MagicMock(multiple_entry_ids=True, entry_ids=entry_ids_mock)
    )

    kegg_rest_mock = mocker.MagicMock(get=mocker.MagicMock(return_value=response_mock))
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)
    single_pull = p.SinglePull(output_dir=output_dir_mock, entry_field=entry_field)
    KEGGrestMock.assert_called_once_with()
    pull_result: p.PullResult = single_pull.pull(entry_ids=entry_ids_mock)
    kegg_rest_mock.get.assert_called_once_with(entry_ids=entry_ids_mock, entry_field=entry_field)

    assert pull_result.successful_entry_ids == tuple(entry_ids_mock)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()

    for entry_id_mock, expected_file_content in zip(entry_ids_mock, expected_file_contents):
        expected_file_extension = 'txt' if entry_field is None else entry_field
        expected_file = f'{entry_id_mock}.{expected_file_extension}'

        if output_dir_mock.endswith('.zip'):
            with zf.ZipFile(output_dir_mock, 'r') as zip_file:
                actual_file_content: str = zip_file.read(expected_file).decode()
        else:
            expected_file: str = os.path.join(output_dir_mock, expected_file)

            with open(expected_file, 'r') as file:
                actual_file_content: str = file.read()

        assert actual_file_content == expected_file_content


@pt.fixture(name='output_dir')
def make_and_remove_output_dir():
    output_dir = 'out-dir/'
    os.mkdir(output_dir)

    yield output_dir

    sh.rmtree(output_dir)


def test_pull_separate_entries(mocker, output_dir: str):
    success_entry_id = 'success-entry-id'
    failed_entry_id = 'fail-entry-id'
    time_out_entry_id = 'time-out-entry-id'
    entry_ids_mock = [failed_entry_id, success_entry_id, time_out_entry_id]
    get_url_mock = mocker.MagicMock(multiple_entry_ids=True, entry_ids=entry_ids_mock)
    initial_response_mock = mocker.MagicMock(status=r.KEGGresponse.Status.FAILED, kegg_url=get_url_mock)
    entry_response_mock1 = mocker.MagicMock(status=r.KEGGresponse.Status.FAILED)
    expected_file_content = 'successful entry'

    entry_response_mock2 = mocker.MagicMock(
        text_body=expected_file_content, status=r.KEGGresponse.Status.SUCCESS,
        kegg_url=mocker.MagicMock(entry_ids=[success_entry_id])
    )

    entry_response_mock3 = mocker.MagicMock(status=r.KEGGresponse.Status.TIMEOUT)

    get_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.pull.r.KEGGrest.get',
        side_effect=[initial_response_mock, entry_response_mock1, entry_response_mock2, entry_response_mock3]
    )

    single_pull = p.SinglePull(output_dir=output_dir)
    pull_result: p.PullResult = single_pull.pull(entry_ids=entry_ids_mock)

    expected_get_call_kwargs = [
        {'entry_ids': entry_ids_mock, 'entry_field': None}, {'entry_ids': [failed_entry_id], 'entry_field': None},
        {'entry_ids': [success_entry_id], 'entry_field': None}, {'entry_ids': [time_out_entry_id], 'entry_field': None}
    ]

    for call, expected_kwargs in zip(get_mock.call_args_list, expected_get_call_kwargs):
        actual_kwargs: dict = call.kwargs

        assert actual_kwargs == expected_kwargs

    assert pull_result.successful_entry_ids == (success_entry_id,)
    assert pull_result.failed_entry_ids == (failed_entry_id,)
    assert pull_result.timed_out_entry_ids == (time_out_entry_id,)

    with open(f'{output_dir}/{success_entry_id}.txt') as file:
        actual_file_content: str = file.read()

    assert actual_file_content == expected_file_content


@pt.fixture(name='file_name')
def remove_file():
    file_name = 'single-entry-id.image'

    yield file_name

    if os.path.isfile(file_name):
        os.remove(file_name)


@pt.mark.parametrize('status', [r.KEGGresponse.Status.SUCCESS, r.KEGGresponse.Status.FAILED])
def test_single_entry(mocker, file_name: str, status: r.KEGGresponse.Status):
    single_entry_id = 'single-entry-id'
    binary_body_mock = b'binary body mock'

    kegg_response_mock = mocker.MagicMock(
        kegg_url=mocker.MagicMock(entry_ids=[single_entry_id], multiple_entry_ids=False), binary_body=binary_body_mock,
        status=status
    )

    mocker.patch('kegg_pull.rest.KEGGrest.get', return_value=kegg_response_mock)
    single_pull = p.SinglePull(output_dir='.', entry_field='image')
    pull_result: p.PullResult = single_pull.pull(entry_ids=[single_entry_id])

    assert pull_result.timed_out_entry_ids == ()

    if status == r.KEGGresponse.Status.SUCCESS:
        assert pull_result.successful_entry_ids == (single_entry_id,)
        assert pull_result.failed_entry_ids == ()

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
        status=r.KEGGresponse.Status.SUCCESS, text_body=separate_text_body1,
        kegg_url=mocker.MagicMock(entry_ids=[entry_id1, entry_id2])
    )

    separate_response_mock1 = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body=separate_text_body1,
        kegg_url=mocker.MagicMock(entry_ids=[entry_id1])
    )

    separate_response_mock2 = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body=separate_text_body2,
        kegg_url=mocker.MagicMock(entry_ids=[entry_id2])
    )

    get_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.pull.r.KEGGrest.get', side_effect=[separate_response_mock1, separate_response_mock2]
    )

    pull_result = p.PullResult()
    single_pull = p.SinglePull(output_dir='.', entry_field=entry_field)
    single_pull._save_multi_entry_response(kegg_response=initial_kegg_response_mock, pull_result=pull_result)

    assert pull_result.successful_entry_ids == (entry_id1, entry_id2)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()

    expected_get_call_kwargs = [
        {'entry_ids': [entry_id1], 'entry_field': entry_field}, {'entry_ids': [entry_id2], 'entry_field': entry_field}
    ]

    for call, expected_kwargs in zip(get_mock.call_args_list, expected_get_call_kwargs):
        actual_kwargs: dict = call.kwargs

        assert actual_kwargs == expected_kwargs

    for entry_id, expected_file_content in zip([entry_id1, entry_id2], [separate_text_body1, separate_text_body2]):
        file_name = f'{entry_id}.{entry_field}'

        with open(file_name, 'r') as file:
            actual_file_content: str = file.read()

        assert actual_file_content == expected_file_content


test_multiple_pull_data = [(p.SingleProcessMultiplePull, {}), (p.MultiProcessMultiplePull, {'n_workers': 2})]
# TODO: Test with force_single_pull with an entry field that can have multiple entries
# TODO: Test with an entry field that can only have one entry without force_single_pull
@pt.mark.parametrize('MultiplePull,kwargs', test_multiple_pull_data)
def test_multiple_pull(mocker, MultiplePull: type, kwargs: dict):
    expected_pull_calls = [
        ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'],
        ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],
        ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
        ['D0', 'D1']
    ]

    entry_ids_mock = list(i.chain.from_iterable(expected_pull_calls))

    expected_successful_entry_ids = (
        'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
        'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'D0'
    )

    expected_failed_entry_ids = ('A9', 'B9', 'C9', 'D1')
    expected_timed_out_entry_ids = ()
    single_pull_mock = PickleableSinglePullMock()

    if MultiplePull is p.SingleProcessMultiplePull:
        single_pull_mock.pull = mocker.spy(single_pull_mock, 'pull')

    multiple_pull = MultiplePull(single_pull=single_pull_mock, **kwargs)
    multiple_pull_result: p.PullResult = multiple_pull.pull(entry_ids=entry_ids_mock)

    assert multiple_pull_result.successful_entry_ids == expected_successful_entry_ids
    assert multiple_pull_result.failed_entry_ids == expected_failed_entry_ids
    assert multiple_pull_result.timed_out_entry_ids == expected_timed_out_entry_ids

    if MultiplePull is p.SingleProcessMultiplePull:
        actual_pull_calls = getattr(single_pull_mock.pull, 'call_args_list')

        for actual_calls, expected_calls in zip(actual_pull_calls, expected_pull_calls):
            assert actual_calls.kwargs == {'entry_ids': expected_calls}


class PickleableSinglePullMock:
    def __init__(self):
        self.entry_field = None

    @staticmethod
    def pull(entry_ids: list):
        successful_entry_ids: list = tuple(entry_ids[:-1])
        failed_entry_ids: list = tuple(entry_ids[-1:])
        single_pull_result = p.PullResult()
        setattr(single_pull_result, '_successful_entry_ids', successful_entry_ids)
        setattr(single_pull_result, '_failed_entry_ids', failed_entry_ids)
        setattr(single_pull_result, '_timed_out_entry_ids', ())

        return single_pull_result


@pt.fixture(name='_')
def teardown():
    yield

    os.remove('pull-results.txt')


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=p, subcommand='pull')


# TODO: Test --help and -h
# TODO: Test from entry ID file and entry ID string
# TODO: Test pull single
def test_main(mocker, _):
    database_mock = 'brite'
    mocker.patch('sys.argv', ['kegg_pull', 'pull', 'multiple', f'--database-name={database_mock}'])
    kegg_rest_mock = mocker.MagicMock()
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)
    single_pull_mock = mocker.MagicMock()
    SinglePullMock = mocker.patch('kegg_pull.pull.SinglePull', return_value=single_pull_mock)
    entry_ids_mock = ['1', '2', '3']
    entry_ids_getter_mock = mocker.MagicMock(from_database=mocker.MagicMock(return_value=entry_ids_mock))
    EntryIdsGetterMock = mocker.patch('kegg_pull.pull.ei.EntryIdsGetter', return_value=entry_ids_getter_mock)

    pull_result_mock = mocker.MagicMock(
        successful_entry_ids=('a', 'b', 'c', 'x'), failed_entry_ids=('y', 'z'), timed_out_entry_ids=()
    )

    pull_mock = mocker.patch('kegg_pull.pull.SingleProcessMultiplePull.pull', return_value=pull_result_mock)
    multiple_pull_mock = mocker.MagicMock(pull=pull_mock)

    SingleProcessMultiplePullMock = mocker.patch(
        'kegg_pull.pull.SingleProcessMultiplePull', return_value=multiple_pull_mock
    )

    p.main()
    KEGGrestMock.assert_called_once_with(n_tries=None, time_out=None, sleep_time=None)
    SinglePullMock.assert_called_once_with(output_dir='.', kegg_rest=kegg_rest_mock, entry_field=None)
    EntryIdsGetterMock.assert_called_once_with(kegg_rest=kegg_rest_mock)
    entry_ids_getter_mock.from_database.assert_called_once_with(database_name=database_mock)
    SingleProcessMultiplePullMock.assert_called_once_with(single_pull=single_pull_mock, force_single_entry=True)
    pull_mock.assert_called_once_with(entry_ids=entry_ids_mock)

    expected_pull_results = '\n'.join([
        '### Successful Entry IDs ###',
        'a',
        'b',
        'c',
        'x',
        '### Failed Entry IDs ###',
        'y',
        'z',
        '### Timed Out Entry IDs ###\n'
     ])

    with open('pull-results.txt', 'r') as file:
        actual_pull_results = file.read()

        assert actual_pull_results == expected_pull_results
