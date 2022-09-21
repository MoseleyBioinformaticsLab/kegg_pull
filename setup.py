import setuptools as st
import src.kegg_pull as kp


def _get_requirements() -> list:
    with open('requirements.txt', 'r') as file:
        requirements: str = file.read()

    requirements: list = requirements.split('\n')
    requirements = [requirement.strip() for requirement in requirements if requirement != '']

    return requirements


def _readme():
    with open('README.rst') as readme_file:
        return readme_file.read()


st.setup(
    name='kegg_pull',
    version=kp.__version__,
    package_dir={'': 'src'},
    install_requires=_get_requirements(),
    entry_points={"console_scripts": ["kegg_pull = kegg_pull.__main__:main"]},
    author='Erik Huckvale',
    author_email='edhu227@g.uky.edu',
    url='https://github.com/MoseleyBioinformaticsLab/KEGGpull',
    long_description_content_type="text/x-rst",
    long_description=_readme()
)
