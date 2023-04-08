# noinspection PyPackageRequirements
import pytest as pt
import typing as t
import jsonschema as js
import kegg_pull.map as kmap
import kegg_pull.kegg_url as ku
import dev.utils as u


@pt.fixture(name='kegg_rest', params=[True, False])
def get_kegg_rest(request, mocker):
    use_kegg_rest = request.param
    if use_kegg_rest:
        yield mocker.MagicMock()
    else:
        yield None


@pt.fixture(name='reverse', params=[True, False])
def get_reverse(request):
    yield request.param


def test_to_dict(mocker, kegg_rest):
    kegg_rest = kegg_rest
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
    kwargs_mock = {'kegg_rest': kegg_rest, 'KEGGurl': ku.EntriesLinkKEGGurl, 'k': 'v'}
    kegg_response_mock = mocker.MagicMock(text_body=text_body_mock)
    request_and_check_error_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.map.r.request_and_check_error', return_value=kegg_response_mock)
    actual_mapping: kmap.KEGGmapping = kmap._to_dict(**kwargs_mock)
    request_and_check_error_mock.assert_called_once_with(**kwargs_mock)
    expected_mapping = {
        'a1': {'b1', 'b2', 'b3'}, 'a2': {'b1', 'b4'}, 'a3': {'b3'}, 'a4': {'b5'}, 'a5': {'b6', 'b7'}}
    assert actual_mapping == expected_mapping


test_map_and_reverse_data = [
    ('database_conv', ku.DatabaseConvKEGGurl, {'kegg_database': 'kegg-db', 'outside_database': 'outside-db'}),
    ('entries_conv', ku.EntriesConvKEGGurl, {'entry_ids': ['e1', 'e2'], 'target_database': 'x'}),
    ('entries_link', ku.EntriesLinkKEGGurl, {'entry_ids': ['e1', 'e2'], 'target_database': 'x'})]


@pt.mark.parametrize('method,KEGGurl,kwargs', test_map_and_reverse_data)
def test_map_and_reverse(mocker, method: str, KEGGurl: type, kwargs: dict, reverse: bool, kegg_rest):
    expected_mapping = {'k': {'v1', 'v2'}}
    to_dict_mock = mocker.patch('kegg_pull.map._to_dict', return_value=expected_mapping)
    # noinspection PyUnresolvedReferences
    method: t.Callable = kmap.__getattribute__(method)
    actual_mapping: kmap.KEGGmapping = method(reverse=reverse, kegg_rest=kegg_rest, **kwargs)
    to_dict_mock.assert_called_once_with(KEGGurl=KEGGurl, kegg_rest=kegg_rest, **kwargs)
    if reverse:
        expected_mapping = kmap.reverse(mapping=expected_mapping)
    assert actual_mapping == expected_mapping


test_deduplicate_pathway_ids_data = [
    {'source_database': 'pathway', 'target_database': 'x'}, {'source_database': 'x', 'target_database': 'pathway'}]


@pt.mark.parametrize('kwargs', test_deduplicate_pathway_ids_data)
def test_deduplicate_pathway_ids(mocker, kwargs: dict, kegg_rest):
    kwargs['kegg_rest'] = kegg_rest
    to_dict_return = {'path:map1': {'x1'}, f'path:ko1': {'x1'}, 'path:map2': {'x2', 'x3'}, 'path:ko2': {'x2', 'x3'}}
    pathway_is_target = kwargs['target_database'] == 'pathway'
    to_dict_return = kmap.reverse(mapping=to_dict_return) if pathway_is_target else to_dict_return
    to_dict_mock = mocker.patch('kegg_pull.map._to_dict', return_value=to_dict_return)
    actual_mapping = kmap.database_link(deduplicate=True, **kwargs)
    to_dict_mock.assert_called_once_with(KEGGurl=ku.DatabaseLinkKEGGurl, **kwargs)
    expected_mapping = {'path:map1': {'x1'}, 'path:map2': {'x2', 'x3'}}
    expected_mapping = kmap.reverse(mapping=expected_mapping) if pathway_is_target else expected_mapping
    assert actual_mapping == expected_mapping


def test_deduplicate_pathway_ids_exception(mocker):
    message = f'Cannot deduplicate path:map entry ids when neither the source database nor the target database is set to "pathway".' \
              f' Databases specified: module, ko.'
    mocker.patch('kegg_pull.map._to_dict')
    with pt.raises(ValueError) as error:
        kmap.database_link(source_database='module', target_database='ko', deduplicate=True)
    u.assert_exception(expected_message=message, exception=error)


@pt.fixture(name='mapping_data', params=[(True, True), (False, True), (True, False), (False, False)])
def get_mapping_data(request, mocker):
    add_glycans, add_drugs = request.param

    def mapping_data(kegg_rest: mocker.MagicMock | None, kwargs: dict) -> tuple:
        compound_is_target = kwargs['target_database'] == 'compound'
        expected_call_args_list = [kwargs]
        compound_to_x = {'cpd1': {'x1', 'x2'}, 'cpd2': {'x1'}, 'cpd3': {'x2'}, 'cpd4': {'x3'}, 'cpd5': {'x2'}, 'cpd6': {'x4'}}
        to_dict_side_effect = [kmap.reverse(mapping=compound_to_x) if compound_is_target else compound_to_x]
        if add_glycans:
            expected_call_args_list.extend([
                {'source_database': 'compound', 'target_database': 'glycan'}, {'source_database': 'glycan', 'target_database': 'x'}])
            to_dict_side_effect.extend([
                {'cpd1': {'gl1'}, 'cpd7': {'gl1', 'gl3'}, 'cpd8': {'gl2'}, 'cpd9': {'gl2'}, 'cpd10': {'gl3'}, 'cpd11': {'gl4'}},
                {'gl1': {'x1', 'x5'}, 'gl2': {'x2', 'x5'}, 'gl4': {'x3'}, 'gl3': {'x3'}, 'gl5': {'x6'}}])
        if add_drugs:
            expected_call_args_list.extend([
                {'source_database': 'compound', 'target_database': 'drug'}, {'source_database': 'drug', 'target_database': 'x'}])
            to_dict_side_effect.extend([
                {'cpd4': {'d1'}, 'cpd3': {'d1'}, 'cpd6': {'d2'}, 'cpd5': {'d2'}, 'cpd12': {'d4'}, 'cpd13': {'d4'}, 'cpd14': {'d5'}},
                {'d1': {'x1', 'x5'}, 'd2': {'x2', 'x5'}, 'd3': {'x3'}, 'd4': {'x3'}, 'd5': {'x6'}, 'd6': {'x6'}}])
        expected_call_args_list = [{
            'source_database': d['source_database'], 'target_database': d['target_database'],
            'kegg_rest': kegg_rest, 'KEGGurl': ku.DatabaseLinkKEGGurl} for d in expected_call_args_list]
        if add_glycans and add_drugs:
            expected_mapping = {
                'cpd4': {'x1', 'x3', 'x5'}, 'cpd2': {'x1'}, 'cpd3': {'x1', 'x2', 'x5'}, 'cpd1': {'x1', 'x2', 'x5'},
                'cpd7': {'x1', 'x3', 'x5'}, 'cpd8': {'x2', 'x5'}, 'cpd6': {'x2', 'x4', 'x5'}, 'cpd9': {'x2', 'x5'},
                'cpd5': {'x2', 'x5'}, 'cpd12': {'x3'}, 'cpd11': {'x3'}, 'cpd10': {'x3'}, 'cpd13': {'x3'}, 'cpd14': {'x6'}}
        elif not add_glycans and add_drugs:
            expected_mapping = {
                'cpd4': {'x3', 'x5', 'x1'}, 'cpd1': {'x2', 'x1'}, 'cpd3': {'x5', 'x2', 'x1'}, 'cpd2': {'x1'}, 'cpd6': {'x5', 'x4', 'x2'},
                'cpd5': {'x5', 'x2'}, 'cpd12': {'x3'}, 'cpd13': {'x3'}, 'cpd14': {'x6'}}
        elif add_glycans and not add_drugs:
            expected_mapping = {
                'cpd7': {'x3', 'x5', 'x1'}, 'cpd1': {'x5', 'x2', 'x1'}, 'cpd2': {'x1'}, 'cpd8': {'x5', 'x2'}, 'cpd3': {'x2'},
                'cpd9': {'x5', 'x2'}, 'cpd5': {'x2'}, 'cpd11': {'x3'}, 'cpd10': {'x3'}, 'cpd4': {'x3'}, 'cpd6': {'x4'}}
        else:
            expected_mapping = compound_to_x
        expected_mapping = kmap.reverse(mapping=expected_mapping) if compound_is_target else expected_mapping
        return add_glycans, add_drugs, expected_call_args_list, to_dict_side_effect, expected_mapping
    yield mapping_data


test_add_glycans_or_drugs_data = [
    {'source_database': 'compound', 'target_database': 'x'}, {'source_database': 'x', 'target_database': 'compound'}]


@pt.mark.parametrize('kwargs', test_add_glycans_or_drugs_data)
def test_add_glycans_or_drugs(mocker, kegg_rest, mapping_data: t.Callable, kwargs: dict):
    add_glycans, add_drugs, expected_call_args_list, to_dict_side_effect, expected_mapping = mapping_data(
        kegg_rest=kegg_rest, kwargs=kwargs)
    to_dict_mock: mocker.MagicMock = mocker.patch('kegg_pull.map._to_dict', side_effect=to_dict_side_effect)
    # noinspection PyUnresolvedReferences
    actual_mapping: kmap.KEGGmapping = kmap.database_link(add_drugs=add_drugs, add_glycans=add_glycans, kegg_rest=kegg_rest, **kwargs)
    u.assert_call_args(function_mock=to_dict_mock, expected_call_args_list=expected_call_args_list, do_kwargs=True)
    assert actual_mapping == expected_mapping


def test_add_glycans_or_drugs_warning(mocker, caplog):
    mocker.patch('kegg_pull.map._to_dict')
    expected_message = f'Adding compound IDs (corresponding to equivalent glycan and/or drug entries) to a mapping where ' \
                       f'neither the source database nor the target database are "compound". Databases specified: reaction, ko.'
    kmap.database_link(source_database='reaction', target_database='ko', add_glycans=True)
    u.assert_warning(message=expected_message, caplog=caplog)


test_indirect_link_data = ['drugs_and_glycans', 'deduplicate', 'drugs_and_glycans_and_deduplicate', '']


@pt.mark.parametrize('test_case', test_indirect_link_data)
def test_indirect_link(mocker, kegg_rest, test_case: str):
    kegg_rest = kegg_rest
    compound_to_reaction = {'cpd1': {'rn1', 'rn3'}, 'cpd2': {'rn2'}, 'cpd3': {'rn3'}}
    pathway_to_reaction = {
        'path:map1': {'rn1', 'rn3'}, 'path:rn1': {'rn1', 'rn3'}, 'path:map2': {'rn2'}, 'path:rn2': {'rn2'},
        'path:map3': {'rn3'}, 'path:rn3': {'rn3'}}
    reaction_to_gene = {'rn1': {'ko1', 'ko2'}, 'rn4': {'ko4', 'ko3'}, 'rn3': {'ko3'}}
    compound_to_glycan = {'cpd1': {'gl1'}}
    compound_to_drug = {'cpd3': {'d1'}}
    compound_to_gene_expected_call_args_list = [
        {'source_database': 'compound', 'target_database': 'reaction'},
        {'source_database': 'reaction', 'target_database': 'ko'}]
    if test_case == 'drugs_and_glycans':
        glycan_to_gene = {'gl1': {'ko1', 'ko4'}, 'gl2': {'ko5'}}
        drug_to_gene = {'d1': {'ko3', 'ko6'}, 'd2': {'ko7'}}
        expected_call_args_list = compound_to_gene_expected_call_args_list
        expected_call_args_list.extend([
            {'source_database': 'compound', 'target_database': 'glycan'}, {'source_database': 'glycan', 'target_database': 'ko'},
            {'source_database': 'compound', 'target_database': 'drug'}, {'source_database': 'drug', 'target_database': 'ko'}])
        side_effect = [
            compound_to_reaction, reaction_to_gene, compound_to_glycan, glycan_to_gene, compound_to_drug, drug_to_gene]
        to_dict_mock = mocker.patch('kegg_pull.map._to_dict', side_effect=side_effect)
        actual_mapping = kmap.indirect_link(
            source_database='compound', intermediate_database='reaction', target_database='ko', add_glycans=True, add_drugs=True,
            kegg_rest=kegg_rest)
        expected_mapping = {'cpd1': {'ko3', 'ko1', 'ko2', 'ko4'}, 'cpd3': {'ko3', 'ko6'}}
    elif test_case == 'deduplicate':
        expected_call_args_list = [
            {'source_database': 'pathway', 'target_database': 'reaction'}, {'source_database': 'reaction', 'target_database': 'ko'}]
        to_dict_mock = mocker.patch('kegg_pull.map._to_dict', side_effect=[pathway_to_reaction, reaction_to_gene])
        actual_mapping = kmap.indirect_link(
            source_database='pathway', intermediate_database='reaction', target_database='ko', deduplicate=True,
            kegg_rest=kegg_rest)
        expected_mapping = {'path:map1': {'ko3', 'ko1', 'ko2'}, 'path:map3': {'ko3'}}
    elif test_case == 'drugs_and_glycans_and_deduplicate':
        reaction_to_pathway = kmap.reverse(mapping=pathway_to_reaction)
        glycan_to_pathway = {'gl1': {'path:map1', 'path:map4'}, 'gl2': {'path:map5'}}
        drug_to_pathway = {'d1': {'path:map3', 'path:map6'}, 'd2': {'path:map7'}}
        expected_call_args_list = [
            {'source_database': 'compound', 'target_database': 'reaction'}, {'source_database': 'reaction', 'target_database': 'pathway'},
            {'source_database': 'compound', 'target_database': 'glycan'}, {'source_database': 'glycan', 'target_database': 'pathway'},
            {'source_database': 'compound', 'target_database': 'drug'}, {'source_database': 'drug', 'target_database': 'pathway'}]
        side_effect = [
            compound_to_reaction, reaction_to_pathway, compound_to_glycan, glycan_to_pathway, compound_to_drug, drug_to_pathway]
        to_dict_mock = mocker.patch('kegg_pull.map._to_dict', side_effect=side_effect)
        actual_mapping = kmap.indirect_link(
            source_database='compound', intermediate_database='reaction', target_database='pathway',
            deduplicate=True, add_glycans=True, add_drugs=True, kegg_rest=kegg_rest)
        expected_mapping = {
            'cpd1': {'path:map1', 'path:map3', 'path:map4'}, 'cpd2': {'path:map2'}, 'cpd3': {'path:map1', 'path:map3', 'path:map6'}}
    else:
        expected_call_args_list = compound_to_gene_expected_call_args_list
        to_dict_mock = mocker.patch('kegg_pull.map._to_dict', side_effect=[compound_to_reaction, reaction_to_gene])
        actual_mapping = kmap.indirect_link(
            source_database='compound', intermediate_database='reaction', target_database='ko',
            kegg_rest=kegg_rest)
        expected_mapping = {'cpd1': {'ko3', 'ko1', 'ko2'}, 'cpd3': {'ko3'}}
    expected_call_args_list = [{
        'source_database': d['source_database'], 'target_database': d['target_database'], 'kegg_rest': kegg_rest,
        'KEGGurl': ku.DatabaseLinkKEGGurl} for d in expected_call_args_list]
    u.assert_call_args(function_mock=to_dict_mock, expected_call_args_list=expected_call_args_list, do_kwargs=True)
    assert actual_mapping == expected_mapping


test_indirect_link_exception_data = [
    ({'source_database': 'pathway', 'intermediate_database': 'reaction', 'target_database': 'reaction'},
     'The source, intermediate, and target database must all be unique. Databases specified: pathway, reaction, reaction.'),
    ({'source_database': 'reaction', 'intermediate_database': 'reaction', 'target_database': 'reaction'},
     'The source, intermediate, and target database must all be unique. Databases specified: reaction, reaction, reaction.')]


@pt.mark.parametrize('kwargs,error_message', test_indirect_link_exception_data)
def test_indirect_link_exception(kwargs: dict, error_message: str):
    with pt.raises(ValueError) as error:
        kmap.indirect_link(**kwargs)
    u.assert_exception(expected_message=error_message, exception=error)


def test_combine_mappings():
    mapping1 = {'k1': {'v1'}, 'k4': {'v3', 'v4'}, 'k5': {'v6', 'v7'}}
    mapping2 = {'k2': {'v1'}, 'k3': {'v2', 'v3'}, 'k4': {'v3', 'v4'}, 'k5': {'v5', 'v6'}}
    actual_combined_mapping = kmap.combine_mappings(mapping1=mapping1, mapping2=mapping2)
    expected_combined_mapping = {'k1': {'v1'}, 'k4': {'v3', 'v4'}, 'k5': {'v6', 'v7', 'v5'}, 'k2': {'v1'}, 'k3': {'v2', 'v3'}}
    assert actual_combined_mapping == expected_combined_mapping


def test_reverse():
    mapping = {'k1': {'v1', 'v2'}, 'k2': {'v1', 'v3', 'v4'}, 'k3': {'v1', 'v2', 'v3', 'v5'}, 'k4': {'v4', 'v5', 'v6'}}
    expected_reverse_mapping = {
        'v1': {'k1', 'k2', 'k3'}, 'v2': {'k1', 'k3'}, 'v3': {'k2', 'k3'}, 'v4': {'k2', 'k4'}, 'v5': {'k3', 'k4'}, 'v6': {'k4'}}
    actual_reverse_mapping = kmap.reverse(mapping=mapping)
    assert actual_reverse_mapping == expected_reverse_mapping


def test_to_json_string():
    mapping = {'k1': {'v1'}, 'k2': {'v1', 'v2'}, 'k3': {'v3', 'v4'}}
    expected_json_string = '{\n  "k1": [\n    "v1"\n  ],\n  "k2": [\n    "v1",\n    "v2"\n  ],\n  "k3": [\n    "v3",\n    "v4"\n  ]\n}'
    actual_json_string: str = kmap.to_json_string(mapping=mapping)
    assert actual_json_string == expected_json_string


def test_save_to_json(json_file_path: str):
    kmap.save_to_json(mapping={'k1': {'v1'}, 'k2': {'v3', 'v2'}}, file_path=json_file_path)
    u.test_save_to_json(json_file_path=json_file_path, expected_saved_json_object={'k1': ['v1'], 'k2': ['v2', 'v3']})


def test_load_from_json(json_file_path: str):
    u.test_load_from_json(
        json_file_path=json_file_path, saved_object={'k1': ['v1'], 'k2': ['v2', 'v3']}, method=kmap.load_from_json,
        expected_loaded_object={'k1': {'v1'}, 'k2': {'v3', 'v2'}})


test_invalid_save_to_json_data = [{'a': [1]}, {'a': [1.2]}, {'a': [[], []]}, {'a': {}}, {'a': []}, {'': ['b']}]
expected_error_message = 'The mapping must be a dictionary of entry IDs (strings) mapped to a set of entry IDs'


@pt.mark.parametrize('invalid_json_object', test_invalid_save_to_json_data)
def test_invalid_save_to_json(caplog, invalid_json_object: dict):
    with pt.raises(js.exceptions.ValidationError):
        kmap.save_to_json(mapping=invalid_json_object, file_path='xxx.json')
    u.assert_error(
        message=expected_error_message, caplog=caplog)


test_invalid_load_from_json_data = test_invalid_save_to_json_data.copy()
test_invalid_load_from_json_data.extend([
    ['1', '2'], {'a': 'b'}, {'a': [2]}, 'abc', 123, 123.123, {1: 2}, {1.2: 2.3}, {'a': [{}, {}]}, {'a': ['b', 1]},
    {'a': [1.2, 'b']}])


@pt.mark.parametrize('invalid_json_object', test_invalid_load_from_json_data)
def test_invalid_load_from_json(caplog, json_file_path: str, invalid_json_object: list | dict | int | float | str):
    u.test_invalid_load_from_json(
        json_file_path=json_file_path, invalid_json_object=invalid_json_object, method=kmap.load_from_json,
        expected_error_message=expected_error_message, caplog=caplog)
