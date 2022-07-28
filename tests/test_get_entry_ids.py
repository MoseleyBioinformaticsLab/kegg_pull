import kegg_pull.kegg_request as kr
import kegg_pull.get_entry_ids as ge
import kegg_pull.kegg_url as ku


# TODO: Test exceptions raised
# TODO: Test loading from a file
# TODO: Test from an entry IDs string
def test_get_entry_ids(mocker):
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
    mock_get = mocker.MagicMock(return_value=mock_kegg_response)
    mock_kegg_request = mocker.MagicMock(get=mock_get)
    MockKEGGrequest = mocker.patch('kegg_pull.get_entry_ids.kr.KEGGrequest', return_value=mock_kegg_request)
    mock_database_name = 'compound'
    actual_entry_ids: list = ge.from_database(database_name=mock_database_name)
    MockKEGGrequest.assert_called_once_with()
    expected_list_url = f'{ku.BASE_URL}/list/{mock_database_name}'
    mock_get.assert_called_once_with(url=expected_list_url)

    expected_entry_ids = [
        'cpd:C22501', 'cpd:C22502', 'cpd:C22500', 'cpd:C22504', 'cpd:C22506', 'cpd:C22507', 'cpd:C22509', 'cpd:C22510',
        'cpd:C22511', 'cpd:C22512', 'cpd:C22513', 'cpd:C22514'
    ]

    assert actual_entry_ids == expected_entry_ids