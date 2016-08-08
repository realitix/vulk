import abc


class BaseApp(abc.ABC):
    def __init__(self, driver):
        self.driver = driver
