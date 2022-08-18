import setuptools as st


def _get_requirements() -> list:
    with open('requirements.txt', 'r') as file:
        requirements: str = file.read()

    requirements: list = requirements.split('\n')
    requirements = [requirement.strip() for requirement in requirements if requirement != '']

    return requirements


st.setup(
    name='kegg_pull', package_dir={'': 'src'}, install_requires=_get_requirements(),
    entry_points={"console_scripts": ["kegg_pull = kegg_pull.__main__:main"]}
)