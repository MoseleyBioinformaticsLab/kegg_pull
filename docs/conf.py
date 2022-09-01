# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Add the package to the python path so autodoc can import modules so doc strings can be included in the documentation
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# It's recommended that you import the project version from your package's __init__.py file
from kegg_pull import __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'KEGGpull'
copyright = '2022, Erik Huckvale'
author = 'Erik Huckvale'

version = __version__
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autodoc_typehints = 'both'

def process_docstrings(app, what, name, obj, options, lines):
    if what == 'module':
        # Remove the CLI portion of the doc string in modules that provide both an API and CLI.
        module_with_cli_to_remove = {'entry_ids', 'pull', 'rest'}
        module_with_cli_to_remove = {f'kegg_pull.{module}' for module in module_with_cli_to_remove}

        if name in module_with_cli_to_remove:
            del lines[3:]
    elif what == 'class' and obj.__init__.__doc__ is not None:
        # Add the parameter and exception descriptions from the __init__ docstring to the class docstring
        parameter_descriptions: list = obj.__init__.__doc__.split('\n')

        for parameter_description in parameter_descriptions:
            lines.append(parameter_description.strip())

def setup(app):
    app.connect('autodoc-process-docstring', process_docstrings)

autodoc_member_order = 'bysource'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True
