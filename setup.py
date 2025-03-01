from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="adp-py",
    version="0.1.0",
    author="",
    author_email="",
    description="AI Documentation Protocol - Python Implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/adp-py",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "jsonschema>=4.0.0",
        "click>=8.0.0",
        "rich>=12.0.0",
        "graphviz>=0.20.0",
        "networkx>=2.6.0",
        "matplotlib>=3.5.0",
    ],
    entry_points={
        "console_scripts": [
            "adp=adp_py.cli.cli:cli",
        ],
    },
) 