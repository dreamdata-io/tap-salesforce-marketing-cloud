#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="tap-salesforce-marketing-cloud",
    version="1.7.1",
    description="Singer.io tap for extracting data from the ExactTarget API",
    author="Fishtown Analytics",
    url="http://fishtownanalytics.com",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_exacttarget"],
    install_requires=[
        "funcy==1.9.1",
        "singer-python==5.8.1",
        "python-dateutil==2.8.0",
        "voluptuous==0.10.5",
        "salesforce-marketing-cloud-python-sdk @ https://github.com/dreamdata-io/salesforce-marketing-cloud-python-sdk/archive/master.zip",
    ],
    extras_require={
        "test": ["pylint==2.10.2", "astroid==2.7.3", "nose"],
        "dev": ["ipdb==0.11"],
    },
    entry_points="""
    [console_scripts]
    tap-salesforce-marketing-cloud=tap_exacttarget:main
    """,
    packages=find_packages(),
    package_data={"tap_exacttarget": ["schemas/*.json"]},
)
