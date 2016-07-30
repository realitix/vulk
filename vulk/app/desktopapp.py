import importlib

from vulk import exception

class DesktopApp():
    
    def __init__(self, app, config, renderer_names = ["vulkan"]):
        self.app = app
        self.renderer_names = renderer_names
        self.config = config
        
        self.init_app()
        self.run_app()
        
    def init_app():
        for renderer_name in self.renderer_names:
            try:
                renderer_module = importlib.import_module(
                    renderer_name,
                    "vulk.graphic.renderer")
                self.renderer = renderer_module.renderer()
            except exception.VulkException:
                self.renderer = None
            else:
                break
        else:
            raise exception.VulkException("Can't load renderer in %s" %
                str(self.renderer_names))
                
        app.init()
    
    def run_app():
        running = True
        renderer.init_window()
        
        while running:
            running = app.render(renderer)
            
        
