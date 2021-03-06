from setuptools import setup, find_packages
from distutils.cmd import Command
from subprocess import call
import os

import vulk


class DocCommand(Command):
    '''Generate doc with mkdocs'''

    description = "Generate documentation"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Generate doc
        call(['mkdocs', 'build', '-q', '-d', 'vulk-doc'])
        # Add readme
        with open('vulk-doc/README.md', 'w') as f:
            f.write('# Vulk Documentation\n\n')
            f.write('[LINK TO DOCUMENTATION]')
            f.write('(https://realitix.github.io/vulk-doc)\n\n')
            f.write('[LINK TO VULK ENGINE]')
            f.write('(https://github.com/realitix/vulk)')


setup(
    name="vulk",
    version=vulk.__version__,
    packages=find_packages(),
    author="realitix",
    author_email="realitix@gmail.com",
    description="Vulk: Advanced 3D engine",
    long_description='Go to http://github.com/realitix/vulk',
    install_requires=['vulkbare', 'docopt', 'numpy', 'pysdl2', 'vulkan',
                      'pyshaderc', 'path.py'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
    url="http://github.com/realitix/vulk",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        'Programming Language :: Python :: Implementation :: CPython',
        "Topic :: Multimedia :: Graphics :: 3D Rendering"
    ],
    license="Apache 2.0",
    cmdclass={'doc': DocCommand}
)
