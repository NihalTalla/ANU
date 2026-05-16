"""
Setup script for Anu AI ecosystem.
"""
import os
import sys
from setuptools import setup, find_packages

# Get version from shared constants
sys.path.insert(0, os.path.abspath("."))
from shared.constants import APP_VERSION

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="anu-ai",
    version=APP_VERSION,
    description="An advanced AI assistant ecosystem designed to operate locally on your Windows laptop",
    author="Anu AI",
    author_email="info@anu-ai.com",
    url="https://github.com/anu-ai/anu",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "anu-api=anu_api.main:main",
            "anu-assistant=anu_assistant.main:main",
            "anu-desktop=anu_desktop.main:main",
            "anu-code-generator=anu_code_generator.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
)