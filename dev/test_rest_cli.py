# noinspection PyPackageRequirements
import pytest as pt
import typing as t
import kegg_pull.rest as r
import kegg_pull.rest_cli as r_cli
import kegg_pull.kegg_url as ku
import dev.utils as u


def test_help(mocker):
    u.assert_help(mocker=mocker, module=r_cli, subcommand='rest')


test_exception_data = [
    ('The request to the KEGG web API failed with the following URL: url/mock', r.KEGGresponse.Status.FAILED),
    ('The request to the KEGG web API timed out with the following URL: url/mock', r.KEGGresponse.Status.TIMEOUT)]


@pt.mark.parametrize('expected_message,status', test_exception_data)
def test_exception(mocker, expected_message: str, status):
    mocker.patch(
        'kegg_pull.rest.KEGGrest.info', return_value=mocker.MagicMock(status=status, kegg_url=mocker.MagicMock(url='url/mock')))
    mocker.patch('sys.argv', ['kegg_pull', 'rest', 'info', 'db-name'])
    with pt.raises(RuntimeError) as error:
        r_cli.main()
    u.assert_exception(expected_message=expected_message, exception=error)


test_args = [
    ['rest', 'info', 'ligand'], ['rest', 'list', 'module'], ['rest', 'get', 'x,y,z'], ['rest', 'get', ',,,a', '--entry-field=image'],
    ['rest', 'find', 'pathway', 'a,b,c,,,'], ['rest', 'find', 'drug', '--formula=CO2'], ['rest', 'find', 'drug', '--em=20.2'],
    ['rest', 'find', 'drug', '--mw=202'], ['rest', 'find', 'drug', '--em=20.2', '--em=30.3'],
    ['rest', 'find', 'drug', '--mw=202', '--mw=303'], ['rest', 'conv', 'kegg-db', 'out-db'],
    ['rest', 'conv', 'entry-ids', 'eid1,eid2', 'genes'], ['rest', 'link', 'target-db', 'source-db'],
    ['rest', 'link', 'entry-ids', ',x,,,y', 'target-db'], ['rest', 'ddi', 'de1,de2,de3'], ['rest', 'get', '-'],
    ['rest', 'find', 'pathway', '-'], ['rest', 'conv', 'entry-ids', '-', 'genes'], ['rest', 'link', 'entry-ids', '-', 'target-db'],
    ['rest', 'ddi', '-']]
test_kwargs = [
    {'database': 'ligand'}, {'database': 'module'}, {'entry_ids': ['x', 'y', 'z'], 'entry_field': None},
    {'entry_ids': ['a'], 'entry_field': 'image'}, {'database': 'pathway', 'keywords': ['a', 'b', 'c']},
    {'database': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None},
    {'database': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None},
    {'database': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202},
    {'database': 'drug', 'formula': None, 'exact_mass': (20.2, 30.3), 'molecular_weight': None},
    {'database': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202, 303)},
    {'kegg_database': 'kegg-db', 'outside_database': 'out-db'},
    {'target_database': 'genes', 'entry_ids': ['eid1', 'eid2']},
    {'target_database': 'target-db', 'source_database': 'source-db'},
    {'target_database': 'target-db', 'entry_ids': ['x', 'y']}, {'drug_entry_ids': ['de1', 'de2', 'de3']}]
test_data = [
    ('rest_cli.r.KEGGrest.info', test_args[0], test_kwargs[0], False, None),
    ('rest_cli.r.KEGGrest.list', test_args[1], test_kwargs[1], False, None),
    ('rest_cli.r.KEGGrest.get', test_args[2], test_kwargs[2], False, None),
    ('rest_cli.r.KEGGrest.get', test_args[3], test_kwargs[3], True, None),
    ('rest_cli.r.KEGGrest.keywords_find', test_args[4], test_kwargs[4], False, None),
    ('rest_cli.r.KEGGrest.molecular_find', test_args[5], test_kwargs[5], False, None),
    ('rest_cli.r.KEGGrest.molecular_find', test_args[6], test_kwargs[6], False, None),
    ('rest_cli.r.KEGGrest.molecular_find', test_args[7], test_kwargs[7], False, None),
    ('rest_cli.r.KEGGrest.molecular_find', test_args[8], test_kwargs[8], False, None),
    ('rest_cli.r.KEGGrest.molecular_find', test_args[9], test_kwargs[9], False, None),
    ('rest_cli.r.KEGGrest.database_conv', test_args[10], test_kwargs[10], False, None),
    ('rest_cli.r.KEGGrest.entries_conv', test_args[11], test_kwargs[11], False, None),
    ('rest_cli.r.KEGGrest.database_link', test_args[12], test_kwargs[12], False, None),
    ('rest_cli.r.KEGGrest.entries_link', test_args[13], test_kwargs[13], False, None),
    ('rest_cli.r.KEGGrest.ddi', test_args[14], test_kwargs[14], False, None),
    ('rest_cli.r.KEGGrest.get', test_args[15], test_kwargs[2], False, '\tx\ny\t\n z '),
    ('rest_cli.r.KEGGrest.keywords_find', test_args[16], test_kwargs[4], False, '\t a\n \tb\nc  \n '),
    ('rest_cli.r.KEGGrest.entries_conv', test_args[17], test_kwargs[11], False, 'eid1\neid2'),
    ('rest_cli.r.KEGGrest.entries_link', test_args[18], test_kwargs[13], False, '\nx\n y \n'),
    ('rest_cli.r.KEGGrest.ddi', test_args[19], test_kwargs[14], False, '\t\n\t\tde1\nde2\nde3\n\n  \n  ')]


@pt.mark.parametrize('rest_method,args,kwargs,is_binary,stdin_mock', test_data)
def test_print(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, stdin_mock: str, caplog):
    kegg_response_mock, expected_output = _get_kegg_response_mock_and_expected_output(mocker=mocker, is_binary=is_binary)
    u.test_print(
        mocker=mocker, argv_mock=args, stdin_mock=stdin_mock, method=rest_method, method_return_value=kegg_response_mock,
        method_kwargs=kwargs, module=r_cli, expected_output=expected_output, is_binary=is_binary, caplog=caplog)


def _get_kegg_response_mock_and_expected_output(mocker, is_binary: bool) -> tuple:
    kegg_response_mock: mocker.MagicMock = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body='text body mock', binary_body=b'binary body mock')
    if is_binary:
        expected_output: bytes = kegg_response_mock.binary_body
    else:
        expected_output: str = kegg_response_mock.text_body
    return kegg_response_mock, expected_output


@pt.mark.parametrize('rest_method,args,kwargs,is_binary,stdin_mock', test_data)
def test_file(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, output_file: str, stdin_mock: str):
    kegg_response_mock, expected_output = _get_kegg_response_mock_and_expected_output(mocker=mocker, is_binary=is_binary)
    u.test_file(
        mocker=mocker, argv_mock=args, output_file=output_file, stdin_mock=stdin_mock, method=rest_method,
        method_return_value=kegg_response_mock, method_kwargs=kwargs, module=r_cli, expected_output=expected_output,
        is_binary=is_binary)


@pt.fixture(name='test_result', params=[True, False])
def get_test_result(request):
    yield request.param


test_test_data = [
    (ku.InfoKEGGurl, test_args[0], test_kwargs[0]),
    (ku.ListKEGGurl, test_args[1], test_kwargs[1]),
    (ku.GetKEGGurl, test_args[2], test_kwargs[2]),
    (ku.GetKEGGurl, test_args[3], test_kwargs[3]),
    (ku.KeywordsFindKEGGurl, test_args[4], test_kwargs[4]),
    (ku.MolecularFindKEGGurl, test_args[5], test_kwargs[5]),
    (ku.MolecularFindKEGGurl, test_args[6], test_kwargs[6]),
    (ku.MolecularFindKEGGurl, test_args[7], test_kwargs[7]),
    (ku.MolecularFindKEGGurl, test_args[8], test_kwargs[8]),
    (ku.MolecularFindKEGGurl, test_args[9], test_kwargs[9]),
    (ku.DatabaseConvKEGGurl, test_args[10], test_kwargs[10]),
    (ku.EntriesConvKEGGurl, test_args[11], test_kwargs[11]),
    (ku.DatabaseLinkKEGGurl, test_args[12], test_kwargs[12]),
    (ku.EntriesLinkKEGGurl, test_args[13], test_kwargs[13]),
    (ku.DdiKEGGurl, test_args[14], test_kwargs[14])]


@pt.mark.parametrize('KEGGurl,args,kwargs', test_test_data)
def test_test(mocker, KEGGurl: type[ku.AbstractKEGGurl], args: list, kwargs: dict, test_result: bool):
    test_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest_cli.r.KEGGrest.test', return_value=test_result)
    argv_mock: list = ['kegg_pull'] + args + ['--test']
    mocker.patch('sys.argv', argv_mock)
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    r_cli.main()
    test_mock.assert_called_with(KEGGurl=KEGGurl, **kwargs)
    print_mock.assert_called_once_with(test_result)


@pt.mark.parametrize('rest_method,args,kwargs,is_binary,stdin_mock', test_data)
def test_zip_archive(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, zip_archive_data: tuple, stdin_mock: str):
    kegg_response_mock, expected_output = _get_kegg_response_mock_and_expected_output(mocker=mocker, is_binary=is_binary)
    u.test_zip_archive(
        mocker=mocker, argv_mock=args, zip_archive_data=zip_archive_data, stdin_mock=stdin_mock, method=rest_method,
        method_return_value=kegg_response_mock, method_kwargs=kwargs, module=r_cli, expected_output=expected_output,
        is_binary=is_binary)
