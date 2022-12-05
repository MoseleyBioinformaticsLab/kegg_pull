import pytest as pt
import os
import shutil as sh

import kegg_pull.kegg_url as ku


@pt.fixture(autouse=True)
def mock_organism_set(mocker, request):
    if not 'disable_mock_organism_set' in request.keywords:
        organism_set_mock = {'organism-code', 'organism-T-number'}

        mocker.patch.object(
            ku.AbstractKEGGurl, 'organism_set', organism_set_mock
        )


@pt.fixture(name='output_file', params=['dir/subdir/file.txt', 'dir/file.txt', './file.txt', 'file.txt'])
def output_file_mock(request):
    output_file: str = request.param

    yield output_file

    os.remove(output_file)
    sh.rmtree('dir', ignore_errors=True)


@pt.fixture(name='zip_archive_data', params=['file.txt', 'dir/file.txt', '/file.txt', '/dir/file.txt'])
def remove_zip_archive(request):
    zip_file_name: str = request.param
    zip_archive_path = 'archive.zip'

    yield zip_archive_path, zip_file_name

    os.remove(zip_archive_path)
