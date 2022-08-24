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


test_main_data = [
    (['from-database', 'compound'], 'from_database', {'database_name': 'compound'}),
    (['from-file', 'file.txt'], 'from_file', {'file_path': 'file.txt'}),
    (['from-keywords', 'pathway', 'k1,k2'], 'from_keywords', {'database_name': 'pathway', 'keywords': ['k1', 'k2']}),
    (
        ['from-molecular-attribute', 'drug', '--formula=CO2'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None}
    ),
    (
        ['from-molecular-attribute', 'drug', '--exact-mass=20.2'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None}
    ),
    (
        ['from-molecular-attribute', 'drug', '--molecular-weight=202'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202}
    ),
    (
        ['from-molecular-attribute', 'drug', '--exact-mass=20.2', '--exact-mass=30.3'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': (20.2, 30.3), 'molecular_weight': None}
    ),
    (
        ['from-molecular-attribute', 'drug', '--molecular-weight=202', '--molecular-weight=303'],
        'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202, 303)}
    )
]
@pt.mark.parametrize('args,method,kwargs', test_main_data)
def test_main_print(mocker, args: list, method: str, kwargs: dict):
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    entry_ids_mock: list = _test_main(mocker=mocker, args=args, method=method, kwargs=kwargs)
    for actual_printed_id, expected_printed_id in zip(print_mock.call_args_list, entry_ids_mock):
        (actual_printed_id,) = actual_printed_id.args

        assert actual_printed_id == expected_printed_id


def _test_main(mocker, args: list, method: str, kwargs: dict) -> list:
    argv_mock = ['kegg_pull', 'entry-ids']
    argv_mock.extend(args)
    mocker.patch('sys.argv', argv_mock)
    entry_ids_mock = ['a', 'b']

    get_entry_ids_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.entry_ids.EntryIdsGetter.{method}', return_value=entry_ids_mock
    )

    ei.main()
    get_entry_ids_mock.assert_called_once_with(**kwargs)

    return entry_ids_mock


@pt.fixture(name='output_file')
def output_file_mock():
    output_file = 'output-file-mock.txt'

    yield output_file

    os.remove(output_file)


@pt.mark.parametrize('args,method,kwargs', test_main_data)
def test_main_file(mocker, args: list, method: str, kwargs: dict, output_file: str):
    args.append(f'--output={output_file}')
    entry_ids_mock: list = _test_main(mocker=mocker, args=args, method=method, kwargs=kwargs)
    expected_output = '\n'.join(entry_ids_mock) + '\n'

    with open(output_file, 'r') as file:
        actual_output: str = file.read()

    assert actual_output == expected_output
