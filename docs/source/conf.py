# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ahttp-client"
copyright = "2024-2025, gunyu1019"
author = "gunyu1019"
release = "v2.0.0b2"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]
add_module_names = False

intersphinx_mapping = {
    "py": ("https://docs.python.org/3", None),
    "aio": ("https://docs.aiohttp.org/en/stable/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

templates_path = ["_templates"]
exclude_patterns = []

language = "en"

locale_dirs = ["locale/"]
gettext_compact = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinxawesome_theme"
html_static_path = ["_static"]
html_css_files = ["custom_theme.css"]

# The theme's own default is "bw" (a monochrome Pygments style with no
# syntax colors at all); "default" is the classic high-contrast Sphinx/
# Pygments palette (strong blue keywords, red strings) that reads well on
# this theme's white background.
#
# Deliberately not setting `pygments_style_dark` here: Sphinx emits that
# style behind a raw `@media (prefers-color-scheme: dark)` query, which is
# driven by the OS-level color scheme and is completely independent of the
# ".dark" class this theme's manual toggle actually sets. Whenever a
# visitor's OS prefers dark but the toggle (or its persisted preference)
# resolves to light, that media query still fires and code blocks end up
# dark while the rest of the page stays light. The dark palette instead
# lives entirely in custom_theme.css, scoped to ".dark .highlight", so code
# blocks track the same toggle state as everything else on the page.
pygments_style = "default"

## Template Option
html_title = "ahttp_client"
html_sidebars = {"**": ["sidebar_main_nav_links.html", "global_sidebar_toc.html"]}
