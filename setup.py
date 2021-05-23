import os
import os.path
import platform

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

system = platform.system()

extra_compile_args = []

if system == 'Darwin':
    # Annoyingly, Github's setup-python action is wrongly building CPython
    # with 10.14 as a target, forcing us to use this as our minimum without
    # rebuilding a dozen combinations of CPython and OS X.
    os.environ.setdefault('MACOSX_DEPLOYMENT_TARGET', '10.14')
    extra_compile_args.append('-std=c++11')

build_with_cython = os.getenv('BUILD_WITH_CYTHON')
if build_with_cython and not CYTHON_AVAILABLE:
    print(
        'BUILD_WITH_CYTHON environment variable is set, but cython'
        ' is not available. Falling back to pre-cythonized version if'
        ' available.'
    )
    build_with_cython = False

build_with_system_lib = os.getenv('BUILD_WITH_SYSTEM_LIB')

macros = []
compiler_directives = {}
libraries = []
sources = [
    'simdjson/errors.cpp',
]

if build_with_system_lib:
    libraries.append('simdjson')
else:
    sources.append('simdjson/simdjson.cpp')

if build_with_cython:
    compiler_directives['embedsignature'] = True

    if os.getenv('BUILD_FOR_DEBUG'):
        # Enable line tracing, which also enables support for coverage
        # reporting.
        macros += [
            ('CYTHON_TRACE', 1),
            ('CYTHON_TRACE_NOGIL', 1)
        ]
        compiler_directives['linetrace'] = True

    sources.append('simdjson/csimdjson.pyx')
else:
    sources.append('simdjson/csimdjson.cpp')


extensions = [
    Extension(
        'csimdjson',
        sources,
        define_macros=macros,
        extra_compile_args=extra_compile_args,
        libraries=libraries,
        language='c++',
    )
]

if build_with_cython:
    extensions = cythonize(extensions, compiler_directives=compiler_directives)

setup(
    name='pysimdjson',
    packages=find_packages(),
    version='4.0.0',
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
            'coverage',
            'mypy'
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
        'simdjson': [
            'simdjson/*.pxd',
            '__init__.pyi',
            'py.typed'
        ]
    }
)
