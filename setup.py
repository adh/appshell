#!/usr/bin/env python

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "appshell",
    version = "0.0.1",
    author = "Ales Hakl",
    author_email = "ales@hakl.net",
    description = ("Bootstrap and Flask based application framework"),
    license = "MIT",
    keywords = "flask bootstrap admin",
#    url = "",
    packages=['appshell'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: Flask"
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
    include_package_data=True,
    zip_safe=False,    
    install_requires = [
        "flask",
        "Flask-BabelEx",
        "Flask-Bootstrap",
        "Flask-Login",
        "Flask-SQLAlchemy",
        "Flask-WTF",
        "WTForms-Alchemy",
        "iso8601",
        "XlsxWriter"
    ]
)
