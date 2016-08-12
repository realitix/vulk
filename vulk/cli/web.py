import importlib.util
import os
import shutil
import subprocess
import tarfile
import urllib.request


class WebCompiler():
    brython_name = "brython3.2.7"
    brython_url = ("https://github.com/brython-dev/brython/releases/download/"
                   "3.2.7/Brython3.2.7-20160621-184325.tar.gz")
    vulk_module = "vulk"

    def __init__(self, app_module, template, out_folder):
        self.app_module = app_module
        self.template = template
        self.out_folder = out_folder

        self.launch_dir = os.getcwd()
        self.out_dir = os.path.join(self.launch_dir, self.out_folder)
        self.lib_dir = os.path.join(self.out_dir, self.brython_name,
                                    "Lib", "site-packages")

    def run(self):
        self.prepare_dir()
        self.download_brython()
        self.copy_vulk()
        self.copy_app()
        self.create_html()
        self.clean()

    def prepare_dir(self):
        try:
            os.makedirs(self.out_dir)
        except FileExistsError:
            pass

    def download_brython(self):
        # Check if brython is last version
        if self.brython_name not in os.listdir(self.out_dir):
            # Download brython to temp file
            gz_path, _ = urllib.request.urlretrieve(self.brython_url)
            with tarfile.open(gz_path, 'r:gz') as gz:
                extracted_name = os.path.dirname(gz.getmembers()[0].name)
                extracted_folder = os.path.dirname(gz_path)
                gz.extractall(extracted_folder)
                os.rename(os.path.join(extracted_folder, extracted_name),
                          os.path.join(self.out_dir, self.brython_name))

    def copy_vulk(self):
        # Copy vulk
        vulk_path = os.path.dirname(
            importlib.util.find_spec(self.vulk_module).origin)
        dest_dir = os.path.join(self.lib_dir, self.vulk_module)
        try:
            shutil.rmtree(dest_dir)
        except FileNotFoundError:
            pass
        shutil.copytree(vulk_path, dest_dir)

    def copy_app(self):
        app = importlib.util.find_spec(self.app_module)
        if not app:
            raise ImportError("{} not found".format(self.app_module))

        app_path = os.path.dirname(app.origin)
        try:
            shutil.rmtree(os.path.join(self.out_dir, self.app_module))
        except FileNotFoundError:
            pass
        shutil.copytree(app_path, os.path.join(self.out_dir, self.app_module))

    def create_html(self):
        with open(os.path.join(self.launch_dir, self.template)) as f:
            content = f.read()
        content = content.format(self.brython_name)

        with open(os.path.join(self.out_dir, "index.html"), "w") as html_file:
            html_file.write(content)

    def clean(self):
        subprocess.run(["py3clean", self.out_dir])


def main(app_module, template, out_folder):
    compiler = WebCompiler(app_module, template, out_folder)
    compiler.run()
