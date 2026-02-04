
import os
import sys
import django

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('..\\..'))  # helpful on Windows

os.environ['DJANGO_SETTINGS_MODULE'] = 'news_app_project.settings'
django.setup()


project = 'Django News Application'
copyright = '2026, Arno'
author = 'Arno'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
