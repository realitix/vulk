"""Vulk 3D engine

Cross-plateform 3D engine
"""
# flake8: noqa

from os import path as p

from vulk.baseapp import *


__version__ = "0.2.0"

PATH_VULK = p.dirname(p.abspath(__file__))
PATH_VULK_ASSET = p.join(PATH_VULK, 'asset')
PATH_VULK_SHADER = p.join(PATH_VULK_ASSET, 'shader')
