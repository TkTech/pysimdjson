#!/usr/bin/env python
import os
import os.path
import sys
import platform
from collections import namedtuple

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext


class BuildAssist(build_ext):
    """Allows overriding (or extending) the configuration for building C/C++
    extensions based on the compiler & platform.
    """
    # TODO: Keep fleshing this out and make it a separate python package, since
    # it would be useful to others.

    #: If CFLAGS (on gcc/clang) or CL (msvc) is defined in the environment
    #: variables then ignored extra_compile_args set by handlers.
    DO_NOT_REPLACE_CFLAGS = True

    #: If LDFLAGS (on gcc/clang) or LINK (msvc) is defined in the environment
    #: variables then ignored extra_link_args set by handlers.
    DO_NOT_REPLACE_LDFLAGS = True

    def build_extensions(self):
        # If a more precise handler is available, use it first. If it isn't,
        # try using a compiler-specific handler.
        compiler_handler = getattr(
            self,
            'using_{cc}_on_{platform}'.format(
                cc=self.compiler.compiler_type,
                platform=self.platform
            ),
            getattr(
                self,
                'using_{cc}'.format(
                    cc=self.compiler.compiler_type
                ),
                None
            )
        )
        if compiler_handler:
            try:
                result = compiler_handler(self.compiler)
            except NotImplementedError:
                print(
                    '[build_assist] No C/C++ handler found for {cc}'
                    ' on {platform}'.format(
                        cc=self.compiler.compiler_type,
                        platform=self.platform
                    )
                )
            else:
                if 'extra_compile_args' in result:
                    if (
                        self.DO_NOT_REPLACE_CFLAGS and
                        (os.environ.get('CFLAGS') or os.environ.get('CL'))
                    ):
                        print(
                            '[build_assist] CFLAGS/CL is set in environment,'
                            ' so default compiler arguments of {flags!r} will'
                            ' not be used.'.format(
                                flags=result['extra_compile_args']
                            )
                        )
                    else:
                        for e in self.extensions:
                            e.extra_compile_args = result['extra_compile_args']

                if 'extra_link_args' in result:
                    if (
                        self.DO_NOT_REPLACE_LDFLAGS and
                        (os.environ.get('LDFLAGS') or os.environ.get('LINK'))
                    ):
                        print(
                            '[build_assist] LDFLAGS/LINK is set in'
                            ' environment, so default linker arguments of'
                            ' {flags!r} will not be used.'.format(
                                flags=result['extra_link_args']
                            )
                        )
                    else:
                        for e in self.extensions:
                            e.extra_link_args = result['extra_link_args']

        super(BuildAssist, self).build_extensions()

    @property
    def platform(self):
        if sys.platform == 'win32':
            return 'windows'
        return os.uname()[0].lower()

    @property
    def darwin_version(self):
        # platform.mac_ver returns a result on platforms *other* than OS X,
        # make sure we're actually on it first...
        if self.platform == 'darwin':
            return namedtuple('mac_ver', ['major', 'minor', 'bugfix'])(
                *(int(v) for v in platform.mac_ver()[0].split('.'))
            )


class SIMDJsonBuild(BuildAssist):
    def using_msvc(self, compiler):
        return {
            'extra_compile_args': [
                '/std:c++17',
                '/arch:AVX2'
            ]
        }

    def using_unix(self, compiler):
        return {
            'extra_compile_args': [
                '-std=c++17',
                '-march=native'
            ]
        }

    def using_unix_on_darwin(self, compiler):
        if self.darwin_version.major >= 10 and self.darwin_version.minor >= 7:
            # After OS X Lion libstdc is deprecated, so we need to make sure we
            # link against libc++ instead.
            return {
                'extra_compile_args': [
                    '-march=native',
                    '-stdlib=libc++'
                ],
                'extra_link_args': [
                    '-lc++',
                    '-nodefaultlibs'
                ]
            }

        return {
            'extra_compile_args': [
                '-std=c++17',
                '-march=native'
            ]
        }


# Do not use wildcards on *any* paths in extensions, as they won't be expanded
# on Windows causing build failures.
try:
    from Cython.Build import cythonize
except ImportError:
    # If Cython isn't available we'll build from the pre-generated cpp sources.
    extensions = [
        Extension(
            'simdjson.csimdjson',
            sources=[
                'simdjson/csimdjson.cpp'
            ],
            language='c++'
        )
    ]
else:
    extensions = cythonize([
        Extension(
            'simdjson.csimdjson',
            sources=[
                'simdjson/csimdjson.pyx'
            ],
            language='c++'
        )
    ], compiler_directives={
        # Make sure we embed function signatures as the first line of the
        # docstring so sphinx can pull them out for documentation.
        'embedsignature': True
    })

root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')


setup(
    name='pysimdjson',
    packages=find_packages(),
    version='1.4.1',
    description='simdjson bindings for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='http://github.com/TkTech/pysimdjson',
    keywords=['json', 'simdjson'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    python_requires='>=3.4',
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest>=2.10',
    ],
    extras_require={
        'dev': [
            'Cython',
            'm2r',
            'sphinx',
            'ghp-import',
            'bumpversion'
        ],
    },
    ext_modules=extensions,
    package_data={
        'simdjson': ['simdjson/*.pyd']
    },
    cmdclass={
        'build_ext': SIMDJsonBuild
    }
)
