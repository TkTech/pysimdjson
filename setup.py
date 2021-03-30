import os
import os.path
import sysconfig
import platform

from setuptools import setup, find_packages, Extension
from distutils.version import LooseVersion

try:
    from Cython.Build import cythonize
except ImportError:
    CYTHON_AVAILABLE = False
else:
    CYTHON_AVAILABLE = True


root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')

if (platform.system() == 'Darwin' and
        'MACOSX_DEPLOYMENT_TARGET' not in os.environ):
    # CPython targets the version of OS X it was built with by default,
    # which can be very, very old. So old, it doesn't support C++11, which
    # only came around in OS X 10.9 (Mavericks)
    current_version = platform.mac_ver()[0]
    target_version = sysconfig.get_config_var(
        'MACOSX_DEPLOYMENT_TARGET',
        current_version
    )
    if (LooseVersion(target_version) < '10.9'
            and LooseVersion(current_version) >= '10.9'):
        os.environ['MACOSX_DEPLOYMENT_TARGET'] = '10.9'

if os.getenv('BUILD_WITH_CYTHON') and not CYTHON_AVAILABLE:
    print(
        'BUILD_WITH_CYTHON environment variable is set, but cython'
        ' is not available. Falling back to pre-cythonized version if'
        ' available.'
    )

if os.getenv('BUILD_WITH_CYTHON') and CYTHON_AVAILABLE:
    macros = []
    compiler_directives = {
        'embedsignature': True
    }

    if os.getenv('BUILD_FOR_DEBUG'):
        # Enable line tracing, which also enables support for coverage
        # reporting.
        macros = [
            ('CYTHON_TRACE', 1),
            ('CYTHON_TRACE_NOGIL', 1)
        ]
        compiler_directives['linetrace'] = True

    extensions = cythonize([
        Extension(
            'csimdjson',
            [
                'simdjson/simdjson.cpp',
                'simdjson/errors.cpp',
                'simdjson/csimdjson.pyx'
            ],
            define_macros=macros
        )
    ], compiler_directives=compiler_directives)
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
            'pytest',
            'pytest-benchmark',
            'flake8',
            'coverage'
        ],
        # Dependencies for running benchmarks.
        'benchmark': [
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
        'simdjson': ['simdjson/*.pxd']
    }
)
