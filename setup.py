from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="ghana-nlp",  # Package name on PyPI
    version="0.2.0",
    author="Prince Larbi",
    author_email="phiddyconcept@gmail.com",
    description="A Python library for interacting with the GhanaNLP APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PhidLarkson/ghananlp-python",

    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.9",
    install_requires=[
        "requests"
    ],
     project_urls={  # Additional useful links
        "Source": "https://github.com/PhidLarkson/ghananlp-python",
        "Documentation": "https://github.com/PhidLarkson/ghananlp-python#readme",
        "Changelog": "https://github.com/PhidLarkson/ghananlp-python/blob/main/CHANGELOG.md",
        "Issues": "https://github.com/PhidLarkson/ghananlp-python/issues",
    },
)
