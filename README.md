# VULK - Vulkan 3d engine

## Project status

[![Build Status](https://travis-ci.org/realitix/vulk.svg?branch=master)](https://travis-ci.org/realitix/vulk)
[![Coverage Status](https://coveralls.io/repos/github/realitix/vulk/badge.svg?branch=master)](https://coveralls.io/github/realitix/vulk?branch=master)

[Documentation](https://realitix.github.io/vulk-doc/) | [API reference](https://realitix.github.io/vulk-api/) |
[Example of use](https://github.com/realitix/vulk-demo)

## What is it ?

Vulk is a 3D engine aimed to provide the best graphical experience with Vulkan API.
It is written fully in Python. It depends on C modules for the communication with
Vulkan.

## What is the project goal ?

- Easy to use: you don't need to understand Vulkan to use VULK.
- Modular: every single part of the api must be modular.
- Full: you shouldn't need to customize core code, it should suits everyone needs.

## Documentation

Documentation is builded with `mkdocs` and the `material` theme.
After each commit, Travis CI builds the documentation and pushes it in the
`vulk-doc` repository. All the documentation is inside the `docs/` folder.
You can easily contribute to it, it's markdown syntax. Check out the
[mkdocs documentation](http://www.mkdocs.org/).

To build the html documentation (in vulk-doc folder), execute the following commands:

```bash
pip install -r requirements.txt
python setup.py doc
```

## API reference
The API documentation is generated after each commit by Travis CI servers
into the dedicated repo vulk-api. You can check it here:
[API reference](https://realitix.github.io/vulk-api/)


#### API convention

To make a beautiful API documentation, we must respect conventions.
Instead of reinventing the wheel with syntax format, we use the
*Google Style Python Docstrings*. Here a complete example:
[example](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).

## Unit tests

To run the unit tests, execute the following command:

```bash
python setup.py test
```

## Dependancies

- [vulkan](https://github.com/realitix/vulkan): Module to communicate with Vulkan SDK
- [pyshaderc](https://github.com/realitix/pyshaderc): Module to compile GLSL to Spir-V
- [VulkBare](https://github.com/realitix/vulk-bare): Module which provides helper functions

## Stay in touch

You can contact me by opening issue (bug or interesting discussion about
the project). If you want a fast and pleasant talk, join the irc channel:
`#vulk`. I'm connected from 9AM to 6PM (France).
