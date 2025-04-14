from setuptools import setup, find_packages
import os

# Read requirements
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README for the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fastjango",
    version="0.1.0",
    description="A web framework inspired by Django using FastAPI as core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FastJango Team",
    author_email="info@fastjango.example.com",
    url="https://github.com/fastjango/fastjango",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fastjango-admin=fastjango.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    keywords="fastapi, django, web framework",
    project_urls={
        "Documentation": "https://fastjango.readthedocs.io/",
        "Source": "https://github.com/fastjango/fastjango",
        "Tracker": "https://github.com/fastjango/fastjango/issues",
    },
) 