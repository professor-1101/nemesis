"""Nemesis Framework Setup Configuration."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nemesis-automation",
    version="1.0.0",
    author="Professor",
    author_email="asadeghianazar@rpk.ir",
    description="BDD Test Automation Framework with Behave & Playwright",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    packages=find_packages(where="src"),
    package_dir={"": "src"},

    package_data={
        "nemesis": ["templates/*.yaml", "templates/*.ini"],
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    # Dependencies are now in pyproject.toml
    entry_points={
        "console_scripts": [
            "nemesis=nemesis.cli.main:cli",
        ],
    },
)