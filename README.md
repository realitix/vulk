# VULK - Vulkan 3d engine

## Project status

[![Build Status](https://travis-ci.org/realitix/vulk.svg?branch=master)](https://travis-ci.org/js78/vulk)
[![Code Climate](https://codeclimate.com/github/realitix/vulk/badges/gpa.svg)](https://codeclimate.com/github/realitix/vulk)
[![Test Coverage](https://codeclimate.com/github/realitix/vulk/badges/coverage.svg)](https://codeclimate.com/github/realitix/vulk/coverage)
[![Issue Count](https://codeclimate.com/github/realitix/vulk/badges/issue_count.svg)](https://codeclimate.com/github/realitix/vulk)

## What is it ?

Vulk is a 3d engine aimed to provide the best graphical experience with Vulkan API.
It is written in Python with C binding and is based on SDL2.

## What is the project goal ?

- Easy to use: you don't need to understand Vulkan to use VULK.
- Modular: every single part of the api must be modular.
- Full: you shouldn't need to customize core code, it should suits everyone needs.

## Documentation

### API
The API documentation is generated after each commit by Travis CI servers
into the dedicated repo vulk-api. You can check it here:
[API documentation](https://cdn.rawgit.com/realitix/vulk-api/master/vulk/index.html)

To build the API (in vulk-api folder), execute the following commands:

```bash
pip install -r requirements.txt
python setup.py api
```
