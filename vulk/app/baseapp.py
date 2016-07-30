import abc


class BaseApp(abc.ABC):
    def __init__(self, renderers, app):
        self.renderers = renderers
        self.app = app
    
    
