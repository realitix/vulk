from setuptools import setup, find_packages
from distutils.cmd import Command
from subprocess import call
import os

from apigenerator.apicommand import APICommand
import vulk


class ReadmeCommand(Command):
    '''Convert the markdown README to Rest format (for pypi)'''

    description = "Prepare README to pypi"
    user_options = []

    def initialize_options(self):
        import pypandoc
        self.pypandoc = pypandoc

    def finalize_options(self):
        pass

    def run(self):
        app_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(app_path, 'README.rst'), 'w') as result:
            result.write(self.pypandoc.convert(
                os.path.join(app_path, 'README.md'),
                'rst'))


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
    long_description=open("README.rst").read(),
    install_requires=['vulkbare', 'docopt', 'numpy', 'pysdl2', 'cvulkan'],
    setup_requires=[],
    tests_require=[],
    include_package_data=True,
    url="http://github.com/realitix/vulk",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.5",
        'Programming Language :: Python :: Implementation :: CPython',
        "Topic :: Multimedia :: Graphics :: 3D Rendering"
    ],
    license="Apache 2.0",
    cmdclass={'api': APICommand, 'doc': DocCommand, 'readme': ReadmeCommand}
)
