import pytest as pt
import typing as t

import kegg_pull.kegg_request as kr
import kegg_pull.entry_ids as ei
import kegg_pull.kegg_url as ku


test_entry_ids_from_kegg_api_data = [
    (ei.from_database, ku.ListKEGGurl, {'database_name': 'compound'}),
    (ei.from_keywords, ku.KeywordsFindKEGGurl, {'database_name': 'compound', 'keywords': ['kw1', 'kw2']}),
    (
        ei.from_molecular_attribute, ku.MolecularFindKEGGurl,
        {'database_name': 'compound', 'formula': 'M4O3C2K1', 'exact_mass': None, 'molecular_weight': None}
    )
]

# TODO: Test exceptions raised
# TODO: Test loading from a file
@pt.mark.parametrize('entry_ids,KEGGurl,kwargs', test_entry_ids_from_kegg_api_data)
def test_entry_ids_from_kegg_api(mocker, entry_ids: t.Callable, KEGGurl: type, kwargs: dict):
    mock_text_body = '''
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

    mock_kegg_response = mocker.MagicMock(text_body=mock_text_body, status=kr.KEGGresponse.Status.SUCCESS)
    mock_execute_api_operation = mocker.MagicMock(return_value=mock_kegg_response)
    mock_kegg_request = mocker.MagicMock(execute_api_operation=mock_execute_api_operation)
    MockKEGGrequest = mocker.patch('kegg_pull.entry_ids.kr.KEGGrequest', return_value=mock_kegg_request)
    actual_entry_ids: list = entry_ids(**kwargs)
    MockKEGGrequest.assert_called_once_with()
    mock_execute_api_operation.assert_called_once_with(KEGGurl=KEGGurl, **kwargs)

    expected_entry_ids = [
        'cpd:C22501', 'cpd:C22502', 'cpd:C22500', 'cpd:C22504', 'cpd:C22506', 'cpd:C22507', 'cpd:C22509', 'cpd:C22510',
        'cpd:C22511', 'cpd:C22512', 'cpd:C22513', 'cpd:C22514'
    ]

    assert actual_entry_ids == expected_entry_ids


# TODO: Test --help and -h
def test_main(mocker):
    mock_database = 'pathway'

    mocker.patch(
        'sys.argv',
        ['kegg_pull', 'entry-ids', 'from-keywords', mock_database, 'k1,k2']
    )

    mock_entry_ids = ['a', 'b']

    mock_from_keywords: mocker.MagicMock = mocker.patch(
        'kegg_pull.entry_ids.from_keywords', return_value=mock_entry_ids
    )

    mock_print: mocker.MagicMock = mocker.patch('builtins.print')
    ei.main()
    mock_from_keywords.assert_called_once_with(database_name=mock_database, keywords=['k1', 'k2'])

    for actual_printed_id, expected_printed_id in zip(mock_print.call_args_list, mock_entry_ids):
        (actual_printed_id,) = actual_printed_id.args

        assert actual_printed_id == expected_printed_id
