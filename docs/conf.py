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

def skip_organism_set(app, what, name, obj, skip, options) -> bool:
    if name in { 'organism_set', 'add_entry_ids', 'merge_pull_results'}:
        return True

def setup(app):
    app.connect('autodoc-skip-member', skip_organism_set)

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
autoclass_content = 'both'
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
