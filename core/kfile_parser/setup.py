"""Setup script for kfile_parser C++ extension"""
import os
import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class get_pybind_include:
    """Helper class to get pybind11 include path"""
    def __str__(self):
        import pybind11
        return pybind11.get_include()


def get_extra_compile_args():
    """Get platform-specific compile args"""
    if sys.platform == 'win32':
        return ['/std:c++17', '/O2']
    else:
        return ['-std=c++17', '-O3', '-fPIC', '-Wall']


def get_extra_link_args():
    """Get platform-specific link args"""
    if sys.platform == 'darwin':
        return ['-stdlib=libc++']
    return []


ext_modules = [
    Extension(
        'kfile_parser._kfile_parser',
        sources=[
            'src/parser.cpp',
            'src/bindings.cpp',
        ],
        include_dirs=[
            get_pybind_include(),
            'src',
        ],
        language='c++',
        extra_compile_args=get_extra_compile_args(),
        extra_link_args=get_extra_link_args(),
    ),
]


class BuildExt(build_ext):
    """Custom build_ext for setting compiler flags"""
    def build_extensions(self):
        # Suppress numpy warnings
        for ext in self.extensions:
            ext.define_macros = [
                ('PYBIND11_DETAILED_ERROR_MESSAGES', None),
            ]
        build_ext.build_extensions(self)


setup(
    name='kfile_parser',
    version='0.1.0',
    author='KooMesh Team',
    description='High-performance LS-DYNA K-file parser using pybind11',
    long_description=open('DEVELOPMENT_PLAN.md').read() if os.path.exists('DEVELOPMENT_PLAN.md') else '',
    packages=['kfile_parser'],
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
    install_requires=['pybind11>=2.10'],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: C++',
    ],
)
