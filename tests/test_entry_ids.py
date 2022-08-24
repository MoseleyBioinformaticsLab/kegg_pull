import pytest as pt
import typing as t
import os

import kegg_pull.rest as r
import kegg_pull.entry_ids as ei
import tests.utils as u


test_process_response_exception_data = [
    ('The KEGG request failed to get the entry IDs from the following URL: url/mock', r.KEGGresponse.Status.FAILED),
    (
        'The KEGG request timed out while trying to get the entry IDs from the following URL: url/mock',
        r.KEGGresponse.Status.TIMEOUT
    )
]
@pt.mark.parametrize('expected_message,status', test_process_response_exception_data)
def test_process_response_exception(mocker, expected_message: str, status: r.KEGGresponse.Status):
    kegg_response_mock = mocker.MagicMock(kegg_url=mocker.MagicMock(url='url/mock'), status=status)

    with pt.raises(RuntimeError) as error:
        ei.EntryIdsGetter._process_response(kegg_response=kegg_response_mock)

    u.assert_expected_error_message(expected_message=expected_message, error=error)


test_from_kegg_rest_data = [
    (ei.EntryIdsGetter().from_database, 'list', {'database_name': 'compound'}),
    (ei.EntryIdsGetter().from_keywords, 'keywords_find', {'database_name': 'compound', 'keywords': ['kw1', 'kw2']}),
    (
        ei.EntryIdsGetter().from_molecular_attribute, 'molecular_find',
        {'database_name': 'compound', 'formula': 'M4O3C2K1', 'exact_mass': None, 'molecular_weight': None}
    )
]
@pt.mark.parametrize('get_entry_ids,rest_method,kwargs', test_from_kegg_rest_data)
def test_from_kegg_rest(mocker, get_entry_ids: t.Callable, rest_method: str, kwargs: dict):
    text_body_mock = '''
    cpd:C22501	alpha-D-Xylulofuranose
    cpd:C22502	alpha-D-Fructofuranose; alpha-D-Fructose
    cpd:C22500	2,8-Dihydroxyadenine
    cpd:C22504	cis-Alkene
    cpd:C22506	Archaeal dolichyl alpha-D-glucosyl phosphate; Dolichyl alpha-D-glucosyl phosphate
    cpd:C22507	6-Sulfo-D-rhamnose
    cpd:C22509	3',5'-Cyclic UMP; Uridine 3',5'-cyclic monophosphate; cUMP
    cpd:C22510	4-Deoxy-4-sulfo-D-erythrose
    cpd:C22511	4-Deoxy-4-sulfo-D-erythrulose
    cpd:C22512	Solabiose
    cpd:C22513	sn-3-O-(Farnesylgeranyl)glycerol 1-phosphate
    cpd:C22514	2,3-Bis-O-(geranylfarnesyl)-sn-glycerol 1-phosphate
    '''

    kegg_response_mock = mocker.MagicMock(text_body=text_body_mock, status=r.KEGGresponse.Status.SUCCESS)
    rest_method_mock = mocker.patch(f'kegg_pull.entry_ids.r.KEGGrest.{rest_method}', return_value=kegg_response_mock)
    actual_entry_ids: list = get_entry_ids(**kwargs)
    rest_method_mock.assert_called_once_with(**kwargs)

    expected_entry_ids = [
        'cpd:C22501', 'cpd:C22502', 'cpd:C22500', 'cpd:C22504', 'cpd:C22506', 'cpd:C22507', 'cpd:C22509', 'cpd:C22510',
        'cpd:C22511', 'cpd:C22512', 'cpd:C22513', 'cpd:C22514'
    ]

    assert actual_entry_ids == expected_entry_ids


@pt.fixture(name='file_info', params=[True, False])
def file_mock(request):
    is_empty = request.param

    if is_empty:
        file_contents_mock = ''
    else:
        file_contents_mock = '''
        cpd:C22501
        cpd:C22502
        cpd:C22500
        cpd:C22504
        cpd:C22506
        cpd:C22507
        cpd:C22509
        cpd:C22510
        cpd:C22511
        cpd:C22512
        cpd:C22513
        cpd:C22514
        '''

    file_name = 'file-mock.txt'

    with open(file_name, 'w') as file:
        file.write(file_contents_mock)

    yield file_name, is_empty

    os.remove(file_name)


def test_from_file(file_info: str):
    file_name, is_empty = file_info

    if is_empty:
        with pt.raises(ValueError) as error:
            ei.EntryIdsGetter.from_file(file_path=file_name)

        u.assert_expected_error_message(
            expected_message=f'Attempted to get entry IDs from {file_name}. But the file is empty',
            error=error
        )
    else:
        actual_entry_ids: list = ei.EntryIdsGetter.from_file(file_path=file_name)

        expected_entry_ids = [
            'cpd:C22501', 'cpd:C22502', 'cpd:C22500', 'cpd:C22504', 'cpd:C22506', 'cpd:C22507', 'cpd:C22509', 'cpd:C22510',
            'cpd:C22511', 'cpd:C22512', 'cpd:C22513', 'cpd:C22514'
        ]

        assert actual_entry_ids == expected_entry_ids


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=ei, subcommand='entry-ids')


def test_main(mocker):
    database_mock = 'pathway'

    mocker.patch(
        'sys.argv',
        ['kegg_pull', 'entry-ids', 'from-keywords', database_mock, 'k1,k2']
    )

    entry_ids_mock = ['a', 'b']

    from_keywords_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.entry_ids.EntryIdsGetter.from_keywords', return_value=entry_ids_mock
    )

    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    ei.main()
    from_keywords_mock.assert_called_once_with(database_name=database_mock, keywords=['k1', 'k2'])

    for actual_printed_id, expected_printed_id in zip(print_mock.call_args_list, entry_ids_mock):
        (actual_printed_id,) = actual_printed_id.args

        assert actual_printed_id == expected_printed_id
