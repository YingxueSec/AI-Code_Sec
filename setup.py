from setuptools import setup, find_packages

setup(
    name="ai-code-audit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "aiohttp>=3.8.0",
    ],
)
