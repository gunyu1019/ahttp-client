import re

from setuptools import setup

version = ""
with open("ahttp_client/__init__.py") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("version is not set")


extras_require = {
    "test": ["pytest", "pytest-cov"],
    "lint": ["pycodestyle", "black"],
    "docs": ["Sphinx", "sphinxawesome-theme", "sphinx-intl"],
}

setup(
    name="ahttp_client",
    version=version,
    packages=["ahttp_client", "ahttp_client.extension"],
    url="https://github.com/gunyu1019/ahttp-client",
    license="MIT",
    author="gunyu1019",
    author_email="gunyu1019@yhs.kr",
    description="A framework for easy asynchronous HTTP request calling with decorations",
    python_requires=">=3.10",
    extras_require=extras_require,
    long_description=open("README.md", encoding="UTF-8").read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=open("requirements.txt", encoding="UTF-8").read(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: Korean",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
