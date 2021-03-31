import os
import os.path

from setuptools import setup, find_packages, Extension

try:
    from Cython.Build import cythonize
except ImportError:
    CYTHON_AVAILABLE = False
else:
    CYTHON_AVAILABLE = True


root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')

if os.getenv('BUILD_WITH_CYTHON') and not CYTHON_AVAILABLE:
    print(
        'BUILD_WITH_CYTHON environment variable is set, but cython'
        ' is not available. Falling back to pre-cythonized version if'
        ' available.'
    )

if os.getenv('BUILD_WITH_CYTHON') and CYTHON_AVAILABLE:
    extensions = cythonize([
        Extension('csimdjson', [
            'simdjson/simdjson.cpp',
            'simdjson/errors.cpp',
            'simdjson/csimdjson.pyx'
        ])
    ])
else:
    extensions = [
        Extension('csimdjson', [
            'simdjson/simdjson.cpp',
            'simdjson/errors.cpp',
            'simdjson/csimdjson.cpp'
        ], language='c++')
    ]

setup(
    name='pysimdjson',
    packages=find_packages(),
    version='3.2.0',
    description='simdjson bindings for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='http://github.com/TkTech/pysimdjson',
    keywords=['json', 'simdjson', 'simd'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    python_requires='>3.4',
    extras_require={
        # Dependencies for package release.
        'release': [
            'sphinx',
            'furo',
            'ghp-import',
            'bumpversion'
        ],
        # Dependencies for running tests.
        'test': [
            'pytest'
        ],
        # Dependencies for running benchmarks.
        'benchmark': [
            'pytest',
            'pytest-benchmark',
            'orjson',
            'python-rapidjson',
            'simplejson',
            'ujson',
            'yyjson',
            'numpy'
        ]
    },
    ext_modules=extensions,
    package_data={
        'simdjson': ['simdjson/*.pxd', '__init__.pyi', 'py.typed']
    }
)
