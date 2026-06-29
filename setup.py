from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="minerva-plugin",
    version="2.1.0",
    description="Minerva - Flake8 plugin for Python code quality checks (SAST)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="pascal65536",
    author_email="pascal65536@gmail.com",
    url="https://github.com/pascal65536/minerva-plugin",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["settings/*.json"],
    },
    data_files=[
        ("settings", ["settings/plugin.json"]),
    ],
    entry_points={
        "flake8.extension": [
            "MN = minerva_plugin:Minerva",
        ],
    },
    install_requires=[
        "flake8>=3.8.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Framework :: Flake8",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.15",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="flake8 linting code-quality static-analysis sast",
)