import re
from setuptools import setup

version = ""
with open("async_client_decorator/__init__.py") as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
    ).group(1)

if not version:
    raise RuntimeError("version is not set")


setup(
    name="async_client_decorator",
    version=version,
    packages=["async_client_decorator"],
    url="https://github.com/gunyu1019/async_client_decorator",
    license="MIT",
    author="gunyu1019",
    author_email="gunyu1019@yhs.kr",
    description="A framework for easy asynchronous HTTP request calling with decorations",
    python_requires=">=3.10",
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
