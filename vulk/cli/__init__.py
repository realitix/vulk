"""Vulk CLI

Usage:
    vulk web <app-module> [--template=<file> --out-folder=<folder>]
    vulk -h | --help
    vulk --version

Options:
    -h --help              Show this screen
    --version              Show version
    --template=<file>      Web html template file [default: web.html]
    --out-folder=<folder>  Out folder of building [default: build]
"""

import os
import sys

import docopt

import vulk
from vulk.cli import web


def set_python_path():
    sys.path.append(os.getcwd())


def main():
    set_python_path()
    args = docopt.docopt(__doc__, version=vulk.__version__)

    if args['web']:
        web.main(args['<app-module>'],
                 args['--template'],
                 args['--out-folder'])

if __name__ == '__main__':
    main()
