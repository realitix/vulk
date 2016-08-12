import abc


class BaseApp(metaclass=abc.ABCMeta):
    """App must inherit this class

    We can't use abc.ABC because brython does not support python3.4
    """
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @abc.abstractmethod
    def render(self, delta):
        return
