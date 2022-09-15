#!/usr/bin/env python

from setuptools import setup


import os


NAME = 'MrPython'
VERSION = '5.0.2beta'


# Load up the description from README.rst
with open('README.md') as f:
    DESCRIPTION = f.read()


setup(
    name=NAME,
    version=VERSION,
    author='Frederic Peschanski',
    author_email='',
    url='https://github.com/nohtyprm/MrPython',
    description='A simplified programming environment for Python (3.x) - based on IDLE ',
    long_description=DESCRIPTION,
    classifiers=[
		'Framework :: IDLE',
		'Intended Audience :: Education',
		'Programming Language :: Python :: 3',
		'Topic :: Education',
    ],
    packages=['mrpython', 'mrpython.gui', 'mrpython.Search', 'mrpython.typechecking', 'mrpython.studentlib', 'mrpython.studentlib.gfx'],
    package_data={
        'mrpython': ['gui/icons/*',]
    },
    #install_requires=['tornado>=2.0'],
    entry_points={
        'console_scripts': ['mrpython = mrpython.Application:main']
    }
)
