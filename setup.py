#!/usr/bin/env python3
"""
DeepDiver - NotebookLM Podcast Automation System
A Python-based automation tool for creating podcasts from documents using NotebookLM
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="deepdiver",
    version="0.1.0",
    author="Jerry's G.Music Assembly",
    author_email="",
    description="NotebookLM Podcast Automation System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gmusic/deepdiver",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "pyperclip>=1.8.2",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "deepdiver=deepdiver.deepdive:main",
        ],
    },
    include_package_data=True,
    package_data={
        "deepdiver": ["*.yaml", "*.yml"],
    },
)
