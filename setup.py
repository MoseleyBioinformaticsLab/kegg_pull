import setuptools as st
import re


requirements = [
    'docopt',
    'requests'
]


def _readme() -> str:
    with open('README.rst') as readme_file:
        return readme_file.read()


def _get_version() -> str:
    with open('src/kegg_pull/__init__.py', 'r') as fd:
        version: str = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('Cannot find version information')

    return version


st.setup(
    name='kegg_pull',
    version=_get_version(),
    package_dir={'': 'src'},
    packages=st.find_packages('src', exclude=['dev', 'docs']),
    install_requires=requirements,
    entry_points={'console_scripts': ['kegg_pull = kegg_pull.__main__:main']},
    author='Erik Huckvale',
    author_email='edhu227@g.uky.edu',
    url='https://github.com/MoseleyBioinformaticsLab/KEGGpull',
    description='Pulls all entries from all KEGG databases, pulls KEGG entry IDs, and wraps all the KEGG REST API operations.',
    long_description_content_type='text/x-rst',
    long_description=_readme()
)
