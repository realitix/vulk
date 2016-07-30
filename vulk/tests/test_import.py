import pkgutil
import importlib

def import_module(modname, is_package):
    module = importlib.import_module(modname)

    parent_modname = "%s." % modname
    if is_package:
        print(str(module) + " " +modname)
        for _, modname, is_package in pkgutil.iter_modules(module.__path__):
            print(parent_modname + modname)
            import_module(parent_modname + modname, is_package)

def test_import():
    """Try to import all modules and packages"""
    import_module("vulk.app", True)
