import abc


class BaseRenderer(abc.ABC):
    @abc.abstractmethod
    def foo(self):
        pass
