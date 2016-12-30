# VULK - Vulkan 3d engine

## Project status

[![Build Status](https://travis-ci.org/realitix/vulk.svg?branch=master)](https://travis-ci.org/realitix/vulk)

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
You can easily contribute to it, it's markdown syntax.

Check out the [mkdocs documentation](http://www.mkdocs.org/).

## API reference
The API documentation is generated after each commit by Travis CI servers
into the dedicated repo vulk-api. You can check it here:
[API reference](https://realitix.github.io/vulk-api/)

To build the API (in vulk-api folder), execute the following commands:

```bash
pip install -r requirements.txt
python setup.py api
```

#### API convention
To make a beautiful API documentation, we must respect conventions.
The documentation must be in markdown and respect the following syntax:

```markdown
'''
Description of the function

*Parameters:*

- `parameter 1`: Parameters is a list and must be quoted with ` `
- `parameter 2`: The description should be precise and can be on
                 several lines (keep the indentation)

*Returns:*

Here we describe the return value

*Exemple:*

[3 backticks]
Here you can put your code
[3 backticks]

**Note: You can add informations at the end of the docstring,
        The name must be inside the following values:
        [Note|Seealso|Warning|Todo]
'''
```

## Dependancies

- [CVulkan](https://github.com/realitix/cvulkan): C module to communicate with Vulkan SDK
- [VulkBare](https://github.com/realitix/vulk-bare): C module providing helper functions

## Stay in touch

You can contact me by opening issue (bug or interesting discussion about
the project). If you want a fast and pleasant talk, join the irc channel:
`#vulk`. I'm connected from 9AM to 6PM (France).
