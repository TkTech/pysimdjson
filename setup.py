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
    extra_compile_args.append('-std=c++11')

if os.getenv('BUILD_WITH_CYTHON') and not CYTHON_AVAILABLE:
    print(
        'BUILD_WITH_CYTHON environment variable is set, but cython'
        ' is not available. Falling back to pre-cythonized version if'
        ' available.'
    )

macros = [
    ('SIMDJSON_IMPLEMENTATION_FALLBACK', "1"),
]
if os.getenv('BUILD_WITH_CYTHON') and CYTHON_AVAILABLE:
    compiler_directives = {
        'embedsignature': True
    }

    if os.getenv('BUILD_FOR_DEBUG'):
        # Enable line tracing, which also enables support for coverage
        # reporting.
        macros.extend([
            ('CYTHON_TRACE', "1"),
            ('CYTHON_TRACE_NOGIL', "1")
        ])
        compiler_directives['linetrace'] = True

    force = bool(os.getenv('FORCE_REBUILD'))

    extensions = cythonize([
        Extension(
            'csimdjson',
            [
                'simdjson/simdjson.cpp',
                'simdjson/util.cpp',
                'simdjson/csimdjson.pyx'
            ],
            define_macros=macros,
            extra_compile_args=extra_compile_args
        )
    ], compiler_directives=compiler_directives, force=force)
else:
    extensions = [
        Extension(
            'csimdjson',
            [
                'simdjson/simdjson.cpp',
                'simdjson/util.cpp',
                'simdjson/csimdjson.cpp'
            ],
            define_macros=macros,
            extra_compile_args=extra_compile_args,
            language='c++'
        )
    ]

setup(
    name='pysimdjson',
    packages=find_packages(),
    version='6.0.2',
    description='simdjson bindings for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='https://github.com/TkTech/pysimdjson',
    keywords=['json', 'simdjson', 'simd'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    python_requires='>3.5',
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
