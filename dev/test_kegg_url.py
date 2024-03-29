# noinspection PyPackageRequirements
import pytest as pt
import requests as rq
import kegg_pull.kegg_url as ku
import dev.utils as u


test_validate_exception_data = [
    (ku.KeywordsFindKEGGurl, {'database': 'ko', 'keywords': ['keyword'] * 500},
     'The KEGG URL length of 4028 exceeds the limit of 4000'),
    (ku.ListKEGGurl, {'database': 'ligand'},
     'Invalid database name: "ligand". Valid values are: <org>, ag, atc, brite, brite_ja, compound, compound_ja, '
     'dgroup, dgroup_ja, disease, disease_ja, drug, drug_ja, enzyme, genome, glycan, jtc, ko, module, ndc, network, '
     'organism, pathway, rclass, reaction, variant, vg, vp, yj. Where <org> is an organism code or T number.'),
    (ku.InfoKEGGurl, {'database': 'organism'},
     'Invalid database name: "organism". Valid values are: <org>, ag, brite, compound, dgroup, disease, drug, '
     'enzyme, genes, genome, glycan, kegg, ko, ligand, module, network, pathway, rclass, reaction, variant, vg, vp.'
     ' Where <org> is an organism code or T number.'),
    (ku.GetKEGGurl, {'entry_ids': [], 'entry_field': None}, 'Entry IDs must be specified for the KEGG get operation'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': 'invalid-entry-field'},
     'Invalid KEGG entry field: "invalid-entry-field". Valid values are: aaseq, conf, image, json, kcf, kgml, mol, '
     'ntseq.'),
    (ku.GetKEGGurl, {'entry_ids': ['x', 'y'], 'entry_field': 'json'},
     'The KEGG entry field: "json" only supports requests of one KEGG entry at a time but 2 entry IDs are provided'),
    (ku.GetKEGGurl, {'entry_ids': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']},
     f'The maximum number of entry IDs is {ku.GetKEGGurl.MAX_ENTRY_IDS_PER_URL} but 11 were provided'),
    (ku.KeywordsFindKEGGurl, {'database': 'not-brite', 'keywords': []}, 'No search keywords specified'),
    (ku.KeywordsFindKEGGurl, {'database': 'brite', 'keywords': ['x']},
     'Invalid database name: "brite". Valid values are: <org>, ag, atc, brite_ja, compound, compound_ja, dgroup, '
     'dgroup_ja, disease, disease_ja, drug, drug_ja, enzyme, genes, genome, glycan, jtc, ko, ligand, module, ndc, '
     'network, pathway, rclass, reaction, variant, vg, vp, yj. Where <org> is an organism code or T number.'),
    (ku.MolecularFindKEGGurl, {'database': 'glycan'}, 'Invalid molecular database name: "glycan". Valid values are: compound, drug.'),
    (ku.MolecularFindKEGGurl, {'database': 'drug'}, 'Must provide either a chemical formula, exact mass, or molecular weight option'),
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'exact_mass': ()},
     'Exact mass range can only be constructed from 2 values but 0 are provided: '),
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'exact_mass': (1.1, 2.2, 3.3)},
     'Exact mass range can only be constructed from 2 values but 3 are provided: 1.1, 2.2, 3.3'),
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'molecular_weight': ()},
     'Molecular weight range can only be constructed from 2 values but 0 are provided: '),
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'molecular_weight': (10, 20, 30)},
     'Molecular weight range can only be constructed from 2 values but 3 are provided: 10, 20, 30'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'exact_mass': (30.3, 20.2)},
     'The first value in the range must be less than the second. Values provided: 30.3-20.2'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'exact_mass': (10.1, 10.1)},
     'The first value in the range must be less than the second. Values provided: 10.1-10.1'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'molecular_weight': (303, 202)},
     'The first value in the range must be less than the second. Values provided: 303-202'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'molecular_weight': (101, 101)},
     'The first value in the range must be less than the second. Values provided: 101-101'),
    (ku.DatabaseConvKEGGurl, {'kegg_database': 'genes', 'outside_database': ''},
     'Invalid KEGG database: "genes". Valid values are: <org>, compound, drug, glycan. Where <org> is an organism '
     'code or T number.'),
    (ku.DatabaseConvKEGGurl, {'kegg_database': 'drug', 'outside_database': 'glycan'},
     'Invalid outside database: "glycan". Valid values are: chebi, ncbi-geneid, ncbi-proteinid, pubchem, uniprot.'),
    (ku.DatabaseConvKEGGurl, {'kegg_database': 'organism-T-number', 'outside_database': 'pubchem'},
     'KEGG database "organism-T-number" is a gene database but outside database "pubchem" is not.'),
    (ku.DatabaseConvKEGGurl, {'kegg_database': 'compound', 'outside_database': 'ncbi-geneid'},
     'KEGG database "compound" is a molecule database but outside database "ncbi-geneid" is not.'),
    (ku.EntriesConvKEGGurl, {'target_database': 'rclass', 'entry_ids': []},
     'Invalid target database: "rclass". Valid values are: <org>, chebi, compound, drug, genes, glycan, ncbi-geneid,'
     ' ncbi-proteinid, pubchem, uniprot. Where <org> is an organism code or T number.'),
    (ku.EntriesConvKEGGurl, {'target_database': 'chebi', 'entry_ids': []},
     'Entry IDs must be specified for this KEGG "conv" operation'),
    (ku.DatabaseLinkKEGGurl, {'target_database': 'genes', 'source_database': ''},
     'Invalid database name: "genes". Valid values are: <org>, ag, atc, brite, compound, dgroup, disease, drug, '
     'enzyme, genome, glycan, jtc, ko, module, ndc, network, pathway, pubmed, rclass, reaction, variant, vg, vp, yj.'
     ' Where <org> is an organism code or T number.'),
    (ku.DatabaseLinkKEGGurl, {'target_database': 'ndc', 'source_database': 'kegg'},
     'Invalid database name: "kegg". Valid values are: <org>, ag, atc, brite, compound, dgroup, disease, drug, '
     'enzyme, genome, glycan, jtc, ko, module, ndc, network, pathway, pubmed, rclass, reaction, variant, vg, vp, yj.'
     ' Where <org> is an organism code or T number.'),
    (ku.DatabaseLinkKEGGurl, {'target_database': 'drug', 'source_database': 'drug'},
     'The source and target database cannot be identical. Database selected: drug.'),
    (ku.EntriesLinkKEGGurl, {'target_database': 'ligand', 'entry_ids': []},
     'Invalid database name: "ligand". Valid values are: <org>, ag, atc, brite, compound, dgroup, disease, drug, '
     'enzyme, genes, genome, glycan, jtc, ko, module, ndc, network, pathway, pubmed, rclass, reaction, variant, vg, '
     'vp, yj. Where <org> is an organism code or T number.'),
    (ku.EntriesLinkKEGGurl, {'target_database': 'yj', 'entry_ids': []},
     'At least one entry ID must be specified to perform the link operation'),
    (ku.DdiKEGGurl, {'drug_entry_ids': []}, 'At least one drug entry ID must be specified for the DDI operation')]


@pt.mark.parametrize('KEGGurl,kwargs,expected_message', test_validate_exception_data)
def test_validate_exception(KEGGurl: type, kwargs: dict, expected_message: str):
    with pt.raises(ValueError) as error:
        KEGGurl(**kwargs)
    expected_message = f'Cannot create URL - {expected_message}'
    u.assert_exception(expected_message=expected_message, exception=error)


test_validate_warning_data = [
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'formula': 'O3', 'exact_mass': 20.2},
     'Only a chemical formula, exact mass, or molecular weight is used to construct the URL. Using formula...', 'find/compound/O3/formula'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'formula': 'O3', 'molecular_weight': 200},
     'Only a chemical formula, exact mass, or molecular weight is used to construct the URL. Using formula...', 'find/drug/O3/formula'),
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'exact_mass': 20.2, 'molecular_weight': 200},
     'Both an exact mass and molecular weight are provided. Using exact mass...', 'find/compound/20.2/exact_mass')]


@pt.mark.parametrize('KEGGurl,kwargs,expected_message,url', test_validate_warning_data)
def test_validate_warning(KEGGurl: type, kwargs: dict, expected_message: str, url: str, caplog):
    kegg_url: ku.AbstractKEGGurl = KEGGurl(**kwargs)
    u.assert_warning(message=expected_message, caplog=caplog)
    expected_url = f'{ku.BASE_URL}/{url}'
    assert kegg_url.url == expected_url


test_create_rest_options_data = [
    (ku.ListKEGGurl, {'database': 'vg'}, 'list', 'vg'),
    (ku.ListKEGGurl, {'database': 'organism-code'}, 'list', 'organism-code'),
    (ku.ListKEGGurl, {'database': 'organism'}, 'list', 'organism'),
    (ku.InfoKEGGurl, {'database': 'ligand'}, 'info', 'ligand'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': None}, 'get', 'x'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': 'image'}, 'get', 'x/image'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': 'aaseq'}, 'get', 'x/aaseq'),
    (ku.GetKEGGurl, {'entry_ids': ['x', 'y'], 'entry_field': None}, 'get', 'x+y'),
    (ku.GetKEGGurl, {'entry_ids': ['x', 'y', 'z'], 'entry_field': 'ntseq'}, 'get', 'x+y+z/ntseq'),
    (ku.KeywordsFindKEGGurl, {'database': 'organism-T-number', 'keywords': ['key', 'word']}, 'find', 'organism-T-number/key+word'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'formula': 'CH4'}, 'find', 'drug/CH4/formula'),
    (ku.MolecularFindKEGGurl, {'database': 'compound', 'exact_mass': 30.3}, 'find', 'compound/30.3/exact_mass'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'molecular_weight': 300}, 'find', 'drug/300/mol_weight'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'exact_mass': (20.2, 30.3)}, 'find', 'drug/20.2-30.3/exact_mass'),
    (ku.MolecularFindKEGGurl, {'database': 'drug', 'molecular_weight': (200, 300)}, 'find', 'drug/200-300/mol_weight'),
    (ku.DatabaseConvKEGGurl, {'kegg_database': 'organism-code', 'outside_database': 'uniprot'}, 'conv', 'organism-code/uniprot'),
    (ku.DatabaseConvKEGGurl, {'kegg_database': 'glycan', 'outside_database': 'chebi'}, 'conv', 'glycan/chebi'),
    (ku.EntriesConvKEGGurl, {'target_database': 'genes', 'entry_ids': ['x', 'y', 'z']}, 'conv', 'genes/x+y+z'),
    (ku.EntriesConvKEGGurl, {'target_database': 'ncbi-proteinid', 'entry_ids': ['a']}, 'conv', 'ncbi-proteinid/a'),
    (ku.DatabaseLinkKEGGurl, {'target_database': 'pubmed', 'source_database': 'atc'}, 'link', 'pubmed/atc'),
    (ku.EntriesLinkKEGGurl, {'target_database': 'genes', 'entry_ids': ['a', 'b', 'c']}, 'link', 'genes/a+b+c'),
    (ku.EntriesLinkKEGGurl, {'target_database': 'jtc', 'entry_ids': ['x']}, 'link', 'jtc/x'),
    (ku.DdiKEGGurl, {'drug_entry_ids': ['x', 'y']}, 'ddi', 'x+y')]


@pt.mark.parametrize('KEGGurl,kwargs,rest_operation,rest_options', test_create_rest_options_data)
def test_create_rest_options(KEGGurl: type, kwargs: dict, rest_operation: str, rest_options: str):
    kegg_url: ku.AbstractKEGGurl = KEGGurl(**kwargs)
    expected_url = f'{ku.BASE_URL}/{rest_operation}/{rest_options}'
    assert str(kegg_url) == kegg_url.url == expected_url
    if KEGGurl == ku.GetKEGGurl:
        assert kegg_url.__getattribute__('multiple_entry_ids') == (len(kegg_url.__getattribute__('entry_ids')) > 1)


@pt.fixture(name='_')
def reset_organism_set():
    ku.AbstractKEGGurl._organism_set = None


@pt.mark.disable_mock_organism_set
def test_organism_set(mocker, _):
    text_mock = """
        T06555	psyt	Candidatus Prometheoarchaeum syntrophicum	Prokaryotes;Archaea;Lokiarchaeota;Prometheoarchaeum
        T03835	agw	Archaeon GW2011_AR10	Prokaryotes;Archaea;unclassified Archaea
        T03843	arg	Archaeon GW2011_AR20	Prokaryotes;Archaea;unclassified Archaea
    """
    response_mock = mocker.MagicMock(status_code=200, text=text_mock)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_url.rq.get', return_value=response_mock)
    actual_organism_set = ku.AbstractKEGGurl.organism_set
    get_mock.assert_called_once_with(url=f'{ku.BASE_URL}/list/organism', timeout=60)
    expected_organism_set = {'agw', 'T03835', 'T06555', 'T03843', 'psyt', 'arg'}
    assert actual_organism_set == expected_organism_set
    get_mock.reset_mock()
    actual_organism_set = ku.AbstractKEGGurl.organism_set
    get_mock.assert_not_called()
    assert actual_organism_set == expected_organism_set


@pt.mark.parametrize('timeout', [True, False])
@pt.mark.disable_mock_organism_set
def test_organism_set_unsuccessful(mocker, timeout: bool, _):
    get_function_patch_path = 'kegg_pull.kegg_url.rq.get'
    url = f'{ku.BASE_URL}/list/organism'
    error_message = 'The request to the KEGG web API {} while fetching the organism set using the URL: {}'
    if timeout:
        get_mock: mocker.MagicMock = mocker.patch(get_function_patch_path, side_effect=rq.exceptions.Timeout())
        error_message: str = error_message.format('timed out', url)
    else:
        failed_status_code = 404
        get_mock: mocker.MagicMock = mocker.patch(
            get_function_patch_path, return_value=mocker.MagicMock(status_code=failed_status_code))
        error_message: str = error_message.format(f'failed with status code {failed_status_code}', url)
    with pt.raises(RuntimeError) as error:
        ku.AbstractKEGGurl.organism_set()
    get_mock.assert_called_once_with(url=url, timeout=60)
    u.assert_exception(expected_message=error_message, exception=error)
