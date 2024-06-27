import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="explainable",
    version="0.0.1",
    author="Numan Team",
    author_email="kostya@numan.ai",
    description="Visualisations for complex data structures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/numan/explainable",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)