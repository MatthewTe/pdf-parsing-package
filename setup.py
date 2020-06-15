import setuptools
from os import path

here = path.abspath(path.dirname(__file__))

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pdfdbapi",
    version="0.0.4",
    description="A package for converting a pdf to textual data and interacting with a sqlite database",
    long_description=long_description,
    url="https://github.com/MatthewTe/pdf-parsing-package",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha ",
        "Intended Audience :: Developers",
        "Topic :: Data Science :: Pipeline API",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir = {'':'pdf_parsing_package'},
    install_requires=['PyPDF2', 'pdfplumber', 'pandas', 'nltk', 'textdistance']

)
