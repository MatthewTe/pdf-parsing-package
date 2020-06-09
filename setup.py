import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pdf_parser_api",
    version="0.0.2",
    author="MatthewTe",
    author_email="teelucksingh.matthew1@gmail.com",
    description="A package for converting a pdf to textual data and writing to a sqlite database",
    long_description=long_description,
    url="https://github.com/MatthewTe/pdf-parsing-package",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
