from setuptools import setup, find_packages

import vulk

setup(
    name="vulk",
    version=vulk.__version__,
    packages=find_packages(),
    author="realitix",
    author_email="realitix@gmail.com",
    description="Vulk: Advanced 3D engine",
    long_description=open("README.md").read(),
    install_requires=["numpy"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    include_package_data=True,
    url="http://github.com/realitix/vulk",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.5",
        "Topic :: Multimedia :: Graphics :: 3D Rendering"
    ],
    license="Apache",
    entry_points = {'console_scripts': ['vulk = vulk.cli:main']}
)
