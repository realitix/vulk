import importlib

from vulk import exception


class BaseContainer():

    def __init__(self, app, config, driver_names):
        self.app = app
        self.driver = self.get_driver(driver_names)
        self.config = config

    def get_driver(self, driver_names):
        driver = None

        for driver_name in driver_names:
            try:
                driver_module = importlib.import_module(
                    "vulk.graphic.driver.%s" % driver_name)
                driver = driver_module.driver()
            except exception.VulkError:
                pass
            else:
                break
        else:
            raise exception.VulkError(
                "Can't load driver in %s" % str(driver_names))

        return driver
