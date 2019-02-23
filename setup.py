#!/usr/bin/env python
import sys
import os.path

from setuptools import setup, find_packages
from distutils.extension import Extension

BUILD_FLAGS = []
if sys.platform == 'darwin':
    BUILD_FLAGS.extend([
        '-std=c++11',
        '-march=native'
    ])

try:
    from Cython.Build import cythonize
except ImportError:
    extensions = [
        Extension(
            'pysimdjson',
            sources=[
                'pysimdjson.cpp'
            ],
            language='c++',
            extra_compile_args=BUILD_FLAGS
        )
    ]
else:
    extensions = cythonize([
        Extension(
            'pysimdjson',
            sources=[
                'pysimdjson.pyx'
            ],
            language='c++',
            extra_compile_args=BUILD_FLAGS
        )
    ])

root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')


setup(
    name='pysimdjson',
    packages=find_packages(),
    version='1.1.0',
    description='simdjson bindings for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='http://github.com/TkTech/pysimdjson',
    keywords=['json', 'simdjson'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    tests_require=[
        'pytest>=2.10',
        'Cython'
    ],
    ext_modules=extensions,
    package_data = {
        '': ['*.pyd']
    }
)
