"""
Setup script for BuildCLI.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="buildcli",
    version="1.0.0",
    author="BuildCLI Developer",
    author_email="developer@buildcli.example",
    description="A modular command-line interface tool with command chaining support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/buildcli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies - keeping minimal for maximum compatibility
    ],
    extras_require={
        "full": [
            "pyinstaller>=5.0.0",
            "requests>=2.28.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "buildcli=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "modules": ["*.py"],
        "core": ["*.py"],
        "utils": ["*.py"],
    },
    zip_safe=False,
)