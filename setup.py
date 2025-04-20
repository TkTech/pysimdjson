import os
import platform

from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
except ImportError:
    CYTHON_AVAILABLE = False
else:
    CYTHON_AVAILABLE = True


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

setup(ext_modules=extensions)
