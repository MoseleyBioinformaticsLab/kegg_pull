# noinspection PyPackageRequirements
import pytest as pt
import os
import shutil as sh
import kegg_pull.kegg_url as ku


@pt.fixture(autouse=True)
def mock_organism_set(mocker, request):
    if 'disable_mock_organism_set' not in request.keywords:
        organism_set_mock = {'organism-code', 'organism-T-number'}
        mocker.patch.object(ku.AbstractKEGGurl, 'organism_set', organism_set_mock)


@pt.fixture(name='output_file', params=['dir/subdir/file.txt', 'dir/file.txt', './file.txt', 'file.txt'])
def get_output_file(request):
    output_file: str = request.param
    yield output_file
    os.remove(output_file)
    sh.rmtree('dir', ignore_errors=True)


@pt.fixture(name='zip_archive_data', params=['file.txt', 'dir/file.txt', '/file.txt', '/dir/file.txt'])
def get_zip_archive_data(request):
    zip_file_name: str = request.param
    zip_archive_path = 'archive.zip'
    yield zip_archive_path, zip_file_name
    os.remove(zip_archive_path)


@pt.fixture(name='json_file_path', params=[
    'dir/subdir/file.json', 'dir/file.json', './file.json', 'file.json', 'archive.zip:file.json', 'archive.zip:dir/file.json'])
def get_json_file_path(request):
    json_file_path: str = request.param
    yield json_file_path
    if '.zip:' in json_file_path:
        os.remove('archive.zip')
    else:
        os.remove(json_file_path)
    sh.rmtree('dir', ignore_errors=True)
