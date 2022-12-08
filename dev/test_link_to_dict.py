import pytest as pt
import typing as t
import jsonschema as js

import kegg_pull.link_to_dict as ltd
import kegg_pull.kegg_url as ku
import dev.utils as u


def test_reverse_mapping():
    mapping: dict = {
        'k1': {'v1', 'v2'},
        'k2': {'v1', 'v3', 'v4'},
        'k3': {'v1', 'v2', 'v3', 'v5'},
        'k4': {'v4', 'v5', 'v6'}
    }

    expected_reverse_mapping: dict = {
        'v1': {'k1', 'k2', 'k3'},
        'v2': {'k1', 'k3'},
        'v3': {'k2', 'k3'},
        'v4': {'k2', 'k4'},
        'v5': {'k3', 'k4'},
        'v6': {'k4'}
    }

    actual_reverse_mapping: dict = ltd.reverse_mapping(mapping=mapping)

    assert actual_reverse_mapping == expected_reverse_mapping


@pt.fixture(name='kegg_rest', params=[True, False])
def get_kegg_rest(request, mocker):
    use_kegg_rest: bool = request.param

    if use_kegg_rest:
        yield mocker.MagicMock()
    else:
        yield None

test_to_dict_data = [
    (
        'database_link', ku.DatabaseLinkKEGGurl, {'target_database_name': 'targ', 'source_database_name': 'src'},
        {'target_database_name': 'targ', 'source_database_name': 'src'}
    ),
    (
        'entries_link', ku.EntriesLinkKEGGurl, {'target_database_name': 'targ', 'entry_ids': ['e1', 'e2']},
        {'target_database_name': 'targ', 'entry_ids': ['e1', 'e2']}
    ),
    (
        'reaction_to_gene', ku.DatabaseLinkKEGGurl, {}, {'target_database_name': 'ko', 'source_database_name': 'reaction'}
    ),
    (
        'gene_to_reaction', ku.DatabaseLinkKEGGurl, {}, {'target_database_name': 'reaction', 'source_database_name': 'ko'}
    )
]
@pt.mark.parametrize('link_function,KEGGurl,link_kwargs,request_kwargs', test_to_dict_data)
def test_to_dict(mocker, kegg_rest, link_function: str, KEGGurl: type, link_kwargs: dict, request_kwargs: dict):
    link_function: t.Callable = ltd.__getattribute__(link_function)

    text_body_mock = """
        a1\tb1
        a1\tb2
        a1\tb3
        a2\tb1
        a2\tb4
        a3\tb3
        a4\tb5
        a5\tb6
        a5\tb7
    """

    kegg_response_mock = mocker.MagicMock(text_body=text_body_mock)

    request_and_check_error_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.link_to_dict.r.request_and_check_error', return_value=kegg_response_mock
    )

    if kegg_rest:
        actual_mapping: dict = link_function(kegg_rest=kegg_rest, **link_kwargs)
    else:
        actual_mapping: dict = link_function(**link_kwargs)

    request_and_check_error_mock.assert_called_once_with(kegg_rest=kegg_rest, KEGGurl=KEGGurl, **request_kwargs)

    expected_mapping: dict = {
        'a1': {'b1', 'b2', 'b3'},
        'a2': {'b1', 'b4'},
        'a3': {'b3'},
        'a4': {'b5'},
        'a5': {'b6', 'b7'}
    }

    assert actual_mapping == expected_mapping


@pt.fixture(name='mapping_data', params=[(True, True), (False, True), (True, False), (False, False)])
def get_mapping_data(request):
    add_glycans, add_drugs = request.param

    def mapping_data(database: str) -> tuple:
        expected_call_args_list = [{'target_database_name': 'compound', 'source_database_name': database}]

        database_link_side_effect = [
            {'src1': {'cpd1', 'cpd2'}, 'src2': {'cpd1', 'cpd3', 'cpd5'}, 'src3': {'cpd4'}, 'src4': {'cpd6'}}
        ]

        if add_glycans:
            expected_call_args_list.extend(
                [
                    {'target_database_name': 'glycan', 'source_database_name': database},
                    {'target_database_name': 'compound', 'source_database_name': 'glycan'}
                ]
            )

            database_link_side_effect.extend(
                [
                    {'src1': {'gl1'}, 'src2': {'gl2'}, 'src3': {'gl3', 'gl4'}, 'src5': {'gl1', 'gl2'}, 'src6': {'gl5'}},
                    {'gl1': {'cpd1', 'cpd7'}, 'gl2': {'cpd8', 'cpd9'}, 'gl3': {'cpd7', 'cpd10'}, 'gl4': {'cpd11'}}
                ]
            )

        if add_drugs:
            expected_call_args_list.extend(
                [
                    {'target_database_name': 'drug', 'source_database_name': database},
                    {'target_database_name': 'compound', 'source_database_name': 'drug'}
                ]
            )

            database_link_side_effect.extend(
                [
                    {'src1': {'d1'}, 'src2': {'d2'}, 'src3': {'d3', 'd4'}, 'src5': {'d1', 'd2'}, 'src6': {'d5', 'd6'}},
                    {'d1': {'cpd3', 'cpd4'}, 'd2': {'cpd5', 'cpd6'}, 'd4': {'cpd12', 'cpd13'}, 'd5': {'cpd14'}}
                ]
            )

        for expected_call_args in expected_call_args_list:
            expected_call_args['kegg_rest'] = None

        if add_glycans and add_drugs:
            expected_mapping = {
                'src1': {'cpd1', 'cpd2', 'cpd3', 'cpd4', 'cpd7'}, 'src2': {'cpd1', 'cpd3', 'cpd6', 'cpd5', 'cpd8', 'cpd9'},
                'src3': {'cpd4', 'cpd7', 'cpd10', 'cpd11', 'cpd12', 'cpd13'}, 'src4': {'cpd6'},
                'src5': {'cpd1', 'cpd3', 'cpd4', 'cpd5', 'cpd6', 'cpd7', 'cpd8', 'cpd9'}, 'src6': {'cpd14'}
            }
        elif not add_glycans and add_drugs:
            expected_mapping = {
                'src1': {'cpd1', 'cpd2', 'cpd3', 'cpd4'}, 'src2': {'cpd1', 'cpd3', 'cpd5', 'cpd6'},
                'src3': {'cpd4', 'cpd12', 'cpd13'}, 'src4': {'cpd6'}, 'src5': {'cpd3', 'cpd5', 'cpd4', 'cpd6'}, 'src6': {'cpd14'}
            }
        elif add_glycans and not add_drugs:
            expected_mapping = {
                'src1': {'cpd1', 'cpd2', 'cpd7'}, 'src2': {'cpd1', 'cpd3', 'cpd5', 'cpd8', 'cpd9'},
                'src3': {'cpd4', 'cpd7', 'cpd10', 'cpd11'}, 'src4': {'cpd6'}, 'src5': {'cpd1', 'cpd7', 'cpd8', 'cpd9'}
            }
        else:
            [expected_mapping] = database_link_side_effect

        return add_glycans, add_drugs, expected_call_args_list, database_link_side_effect, expected_mapping
    
    yield mapping_data


test_database_to_compound_data = [
    ('compound_to_pathway', True, 'pathway'), ('pathway_to_compound', False, 'pathway'), ('compound_to_reaction', True, 'reaction'),
    ('reaction_to_compound', False, 'reaction')
]
@pt.mark.parametrize('link_function,reverse_mapping,database', test_database_to_compound_data)
def test_database_to_compound(mocker, link_function: str, reverse_mapping: bool, database: str, mapping_data: t.Callable):
    link_function: t.Callable = ltd.__getattribute__(link_function)
    add_glycans, add_drugs, expected_call_args_list, database_link_side_effect, expected_mapping = mapping_data(database=database)

    database_link_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.link_to_dict.database_link', side_effect=database_link_side_effect
    )

    actual_mapping: dict = link_function(add_glycans=add_glycans, add_drugs=add_drugs)
    u.assert_call_args(function_mock=database_link_mock, expected_call_args_list=expected_call_args_list, do_kwargs=True)
    _assert_correct_mapping(actual_mapping=actual_mapping, expected_mapping=expected_mapping, reverse_mapping=reverse_mapping)


def _assert_correct_mapping(actual_mapping: dict, expected_mapping: dict, reverse_mapping: bool) -> None:
    if reverse_mapping:
        expected_mapping: dict = ltd.reverse_mapping(mapping=expected_mapping)

    assert actual_mapping == expected_mapping


test_gene_to_compound_data = [('compound_to_gene', True), ('gene_to_compound', False)]
@pt.mark.parametrize('link_function,reverse_mapping', test_gene_to_compound_data)
def test_gene_to_compound(mocker, link_function: str, reverse_mapping: bool):
    database_link_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.link_to_dict.database_link', return_value={'ko1': {'rn1'}, 'ko2': {'rn1'}, 'ko3': {'rn4', 'rn3'}, 'ko4': {'rn4'}}
    )

    reaction_to_compound_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.link_to_dict.reaction_to_compound', return_value={'rn1': {'cpd1'}, 'rn2': {'cpd2'}, 'rn3': {'cpd1', 'cpd3'}}
    )

    kegg_rest_mock = mocker.MagicMock()
    link_function: t.Callable = ltd.__getattribute__(link_function)
    actual_mapping: dict = link_function(add_glycans=True, add_drugs=False, kegg_rest=kegg_rest_mock)
    reaction_to_compound_mock.assert_called_once_with(add_glycans=True, add_drugs=False, kegg_rest=kegg_rest_mock)
    database_link_mock.assert_called_once_with(target_database_name='reaction', source_database_name='ko', kegg_rest=kegg_rest_mock)
    expected_mapping = {'ko1': {'cpd1'}, 'ko2': {'cpd1'}, 'ko3': {'cpd1', 'cpd3'}}
    _assert_correct_mapping(actual_mapping=actual_mapping, expected_mapping=expected_mapping, reverse_mapping=reverse_mapping)


test_pathway_to_database_data = [
    ('reaction_to_pathway', 'reaction', True, 'path:rn'), ('pathway_to_reaction', 'reaction', False, 'path:rn'),
    ('gene_to_pathway', 'ko', True, 'path:ko'), ('pathway_to_gene', 'ko', False, 'path:ko')
]
@pt.mark.parametrize('link_function,database,reverse_mapping,duplicate_prefix', test_pathway_to_database_data)
def test_pathway_to_database(mocker, link_function: str, database: str, reverse_mapping: bool, duplicate_prefix: str):
    database_link_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.link_to_dict.database_link', return_value={
            'path:map1': {'targ1'}, f'{duplicate_prefix}1': {'targ1'}, 'path:map2': {'targ2', 'targ3'},
            f'{duplicate_prefix}2': {'targ2', 'targ3'}
        }
    )

    link_function: t.Callable = ltd.__getattribute__(link_function)
    actual_mapping: dict = link_function()
    database_link_mock.assert_called_once_with(target_database_name=database, source_database_name='pathway', kegg_rest=None)
    expected_mapping = {'path:map1': {'targ1'}, 'path:map2': {'targ2', 'targ3'}}
    _assert_correct_mapping(actual_mapping=actual_mapping, expected_mapping=expected_mapping, reverse_mapping=reverse_mapping)


def test_to_json_string():
    mapping = {'k1': {'v1'}, 'k2': {'v1', 'v2'}, 'k3': {'v3', 'v4'}}
    expected_json_string = '{\n  "k1": [\n    "v1"\n  ],\n  "k2": [\n    "v1",\n    "v2"\n  ],\n  "k3": [\n    "v3",\n    "v4"\n  ]\n}'
    actual_json_string: str = ltd.to_json_string(mapping=mapping)

    assert actual_json_string == expected_json_string


def test_save_to_json(json_file_path: str):
    ltd.save_to_json(mapping={'k1': {'v1'}, 'k2': {'v3', 'v2'}}, file_path=json_file_path)
    u.test_save_to_json(json_file_path=json_file_path, expected_saved_json_object={'k1': ['v1'], 'k2': ['v2', 'v3']})


def test_load_from_json(json_file_path: str):
    u.test_load_from_json(
        json_file_path=json_file_path, saved_object={'k1': ['v1'], 'k2': ['v2', 'v3']}, method=ltd.load_from_json,
        expected_loaded_object={'k1': {'v1'}, 'k2': {'v3', 'v2'}}
    )


test_invalid_save_to_json_data = [{}, {'a': [1]}, {'a': [1.2]}, {'a': [[], []]}, {'a': {}}, {'a': []}, {'': ['b']}]
expected_error_message = 'The mapping must be a dictionary of KEGG entry IDs (strings) mapped to a set of KEGG entry IDs'


@pt.mark.parametrize('invalid_json_object', test_invalid_save_to_json_data)
def test_invalid_save_to_json(caplog, invalid_json_object: dict):
    with pt.raises(js.exceptions.ValidationError):
        ltd.save_to_json(mapping=invalid_json_object, file_path='xxx.json')

    u.assert_error(
        message=expected_error_message, caplog=caplog
    )


test_invalid_load_from_json_data = test_invalid_save_to_json_data.copy()

test_invalid_load_from_json_data.extend(
    [
        ['1', '2'], {'a': 'b'}, {'a': [2]}, 'abc', 123, 123.123, {1: 2}, {1.2: 2.3}, {'a': [{}, {}]}, {'a': ['b', 1]},
        {'a': [1.2, 'b']}
    ]
)


@pt.mark.parametrize('invalid_json_object', test_invalid_load_from_json_data)
def test_invalid_load_from_json(caplog, json_file_path: str, invalid_json_object: t.Union[list, dict, int, float, str]):
    u.test_invalid_load_from_json(
        json_file_path=json_file_path, invalid_json_object=invalid_json_object, method=ltd.load_from_json,
        expected_error_message=expected_error_message, caplog=caplog
    )
