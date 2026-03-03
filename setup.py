from setuptools import setup, find_packages

setup(
    name="ai-harness",
    version="0.1.0",
    description="Modular AI harness with pluggable providers",
    author="",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "Click>=8.0",
        "PyYAML>=6.0",
        "colorama>=0.4",
    ],
    entry_points={"console_scripts": ["ai-harness=ai_harness.cli.__init__:main"]},
)
