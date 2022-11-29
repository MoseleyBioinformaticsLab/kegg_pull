import pytest as pt
import typing as t
import os

import kegg_pull.rest as r
import kegg_pull.entry_ids as ei
import kegg_pull.kegg_url as ku
import dev.utils as u


test_from_kegg_rest_data = [
    (ei.from_database, ku.ListKEGGurl, {'database_name': 'compound'}, 'list/compound'),
    (ei.from_keywords, ku.KeywordsFindKEGGurl, {'database_name': 'compound', 'keywords': ['kw1', 'kw2']}, 'find/compound/kw1+kw2'),
    (
        ei.from_molecular_attribute, ku.MolecularFindKEGGurl,
        {'database_name': 'compound', 'formula': 'M4O3C2K1', 'exact_mass': None, 'molecular_weight': None},
        'find/compound/M4O3C2K1/formula'
    )
]
@pt.mark.parametrize('get_entry_ids,KEGGurl,kwargs,url', test_from_kegg_rest_data)
def test_from_kegg_rest(mocker, get_entry_ids: t.Callable, KEGGurl: type, kwargs: dict, url: str):
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

    get_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.rest.rq.get',
        return_value=mocker.MagicMock(text=text_body_mock, status_code=200)
    )

    request_and_check_error_spy: mocker.MagicMock = mocker.spy(r, 'request_and_check_error')
    actual_entry_ids: list = get_entry_ids(**kwargs)
    request_and_check_error_spy.assert_called_once_with(kegg_rest=None, KEGGurl=KEGGurl, **kwargs)
    url = f'{ku.BASE_URL}/{url}'
    get_mock.assert_called_once_with(url=url, timeout=60)

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
            ei.from_file(file_path=file_name)

        u.assert_expected_error_message(
            expected_message=f'Attempted to load entry IDs from {file_name}. But the file is empty',
            error=error
        )
    else:
        actual_entry_ids: list = ei.from_file(file_path=file_name)

        expected_entry_ids = [
            'cpd:C22501', 'cpd:C22502', 'cpd:C22500', 'cpd:C22504', 'cpd:C22506', 'cpd:C22507', 'cpd:C22509', 'cpd:C22510',
            'cpd:C22511', 'cpd:C22512', 'cpd:C22513', 'cpd:C22514'
        ]

        assert actual_entry_ids == expected_entry_ids
