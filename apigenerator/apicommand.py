'''Generate html API

pydoc is good but must be used from command line.
We have to copy a lot of code...
'''

from distutils.cmd import Command
import os
from os import path
import codecs


OUT_FOLDER = 'vulk-api'
HERE = path.dirname(path.realpath(__file__))


class APICommand(Command):
    description = "Generate HTML API"
    user_options = []

    def module_file(self, m):
        mbase = path.join(OUT_FOLDER, *m.name.split('.'))
        if m.is_package():
            return path.join(mbase, self.pdoc.html_package_name)
        else:
            return '%s%s' % (mbase, self.pdoc.html_module_suffix)

    def html_out(self, m, html=True):
        f = self.module_file(m)
        if not html:
            f = self.module_file(m).replace(".html", ".md")
        dirpath = path.dirname(f)
        if not os.access(dirpath, os.R_OK):
            os.makedirs(dirpath)
        try:
            with codecs.open(f, 'w+', 'utf-8') as w:
                out = m.html(external_links=False,
                             link_prefix='',
                             http_server=True,
                             source=True)
                print(out, file=w)
        except Exception:
            try:
                os.unlink(f)
            except:
                pass
            raise
        for submodule in m.submodules():
            self.html_out(submodule, html)

    def initialize_options(self):
        import pdoc
        from mock_import import mock_import
        self.pdoc = pdoc
        self.mock_import = mock_import

    def finalize_options(self):
        pass

    def run(self):
        with self.mock_import():
            self.pdoc.tpl_lookup.directories.insert(
                0, path.join(HERE, 'templates'))

            module = self.pdoc.Module(
                self.pdoc.import_module('vulk'),
                docfilter=None,
                allsubmodules=False
            )
            self.html_out(module, True)
