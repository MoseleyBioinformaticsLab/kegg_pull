import pytest as pt
import zipfile as zf
import os
import shutil as sh

import kegg_pull.__main__ as m
import kegg_pull.entry_ids_cli as ei_cli
import kegg_pull.rest_cli as r_cli
import kegg_pull.pull_cli as p_cli


def test_main_help(mocker):
    mocker.patch('sys.argv', ['kegg_pull', '--full-help'])
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    m.main()
    print_mock.assert_any_call(m.__doc__)
    print_mock.assert_any_call(ei_cli.__doc__)
    print_mock.assert_any_call(r_cli.__doc__)
    print_mock.assert_any_call(p_cli.__doc__)
    mocker.patch('sys.argv', ['kegg_pull', '--help'])
    print_mock.reset_mock()
    m.main()
    print_mock.assert_called_once_with(m.__doc__)
    print_mock.reset_mock()
    mocker.patch('sys.argv', ['kegg_pull'])
    m.main()
    print_mock.assert_called_once_with(m.__doc__)


@pt.fixture(name='print_output', params=[True, False])
def print_output_fixture(request):
    print_output: bool = request.param

    yield print_output

    if not print_output:
        os.remove('output.txt')


test_main_entry_ids_data = [
    (['from-database', 'brite'], 'dev/test_data/all-brite-entry-ids.txt'),
    (['from-file', 'dev/test_data/all-brite-entry-ids.txt'], 'dev/test_data/all-brite-entry-ids.txt'),
    (['from-keywords', 'module', 'Guanine,ribonucleotide'], 'dev/test_data/module-entry-ids.txt'),
    (['from-molecular-attribute', 'drug', '--exact-mass=420', '--exact-mass=440'], 'dev/test_data/drug-entry-ids.txt')
]
@pt.mark.parametrize('args,expected_output', test_main_entry_ids_data)
def test_main_entry_ids(mocker, args: list, expected_output: str, print_output: bool):
    args: list = ['kegg_pull', 'entry-ids'] + args
    _test_output(mocker=mocker, args=args, expected_output=expected_output, print_output=print_output, split_lines=True)


def _test_output(mocker, args: list, expected_output: str, print_output: bool, split_lines: bool):
    print_mock = None

    if print_output:
        print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    else:
        args += ['--output=output.txt']

    mocker.patch('sys.argv', args)
    m.main()

    with open(expected_output, 'r') as file:
        expected_output: str = file.read()

    if print_output:
        if split_lines:
            expected_output: list = expected_output.strip().split('\n')

            for call, expected_entry_id in zip(print_mock.call_args_list, expected_output):
                actual_entry_id, = call.args

                assert actual_entry_id == expected_entry_id
        else:
             print_mock.assert_called_once_with(expected_output)
    else:
        with open('output.txt', 'r') as file:
            actual_entry_ids: str = file.read()

        assert expected_output == actual_entry_ids


test_main_rest_data = [
    (['conv', 'glycan', 'pubchem'], 'dev/test_data/glycan-pubchem-conv.txt'),
    (['conv', '--conv-target=pubchem', 'gl:G13143,gl:G13141,gl:G13139'], 'dev/test_data/glycan-pubchem-entry-ids.txt'),
    (['link', 'module', 'pathway'], 'dev/test_data/module-pathway-link.txt'),
    (['link', '--link-target=pathway', 'md:M00575,md:M00574,md:M00363'], 'dev/test_data/pathway-module-entry-ids.txt'),
    (['ddi', 'D00564,D00100,D00109'], 'dev/test_data/ddi-output.txt')
]
@pt.mark.parametrize('args,expected_output', test_main_rest_data)
def test_main_rest(mocker, args: list, expected_output: str, print_output: bool):
    args = ['kegg_pull', 'rest'] + args
    _test_output(mocker=mocker, args=args, expected_output=expected_output, print_output=print_output, split_lines=False)


@pt.fixture(name='output', params=['brite-entries.zip', 'brite-entries'])
def pull_output(request):
    output: str = request.param

    yield output

    if output == 'brite-entries.zip':
        os.remove(output)
    else:
        sh.rmtree(output, ignore_errors=True)


test_main_pull_data = [
    ['--file-path=dev/test_data/brite-entry-ids.txt', '--force-single-entry', '--multi-process', '--n-workers=2'],
    ['--file-path=dev/test_data/brite-entry-ids.txt', '--force-single-entry']
]
@pt.mark.parametrize('args', test_main_pull_data)
def test_main_pull(mocker, args: list, output: str):
    expected_pull_results = '''### Successful Entry IDs ###
br:br08005
br:br08902
### Failed Entry IDs ###
br:br03220
br:br03222
### Timed Out Entry IDs ###
'''

    successful_entry_ids = [
        'br:br08005',
        'br:br08902'
    ]

    args: list = ['kegg_pull', 'pull', 'multiple'] + args + [f'--output={output}']
    mocker.patch('sys.argv', args)
    m.main()

    if output.endswith('.zip'):
        with zf.ZipFile(output, 'r') as actual_zip:
            with zf.ZipFile(f'dev/test_data/{output}', 'r') as expected_zip:
                for successful_entry_id in successful_entry_ids:
                    actual_entry: str = actual_zip.read(successful_entry_id + '.txt').decode()
                    expected_entry: str = expected_zip.read(successful_entry_id + '.txt').decode()

                    assert actual_entry == expected_entry
    else:
        for successful_entry_id in successful_entry_ids:
            with open(f'{output}/{successful_entry_id}.txt') as actual_file:
                with open(f'dev/test_data/{output}/{successful_entry_id}.txt') as expected_file:
                    actual_entry: str = actual_file.read()
                    expected_entry: str = expected_file.read()

            assert actual_entry == expected_entry

    with open('pull-results.txt', 'r') as file:
        actual_pull_results: str = file.read()

    assert actual_pull_results == expected_pull_results