"""
Setup script pour llm-cli.

Ce script permet l'installation du package en mode développement avec pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="llm-cli",
    version="0.1.0",
    description="A CLI tool for interacting with OpenRouter API",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "typer",
        "rich",
        "requests",
        "pydantic",
        "tenacity",
    ],
    entry_points={
        "console_scripts": [
            "llm=llm.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)