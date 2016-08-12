from browser import document, window

from vulk.graphic.driver import webgl


class WebContainer():
    """Launch app on web

    WebContainer should inherit from basecontainer but
    we have to wait for the version 3.2.8 of brython
    """

    def __init__(self, app, user_config=None, driver_names=("webgl2")):
        config = {
            'canvas_id': 'app_canvas'
        }
        config.update(user_config if user_config else {})

        if not config.get('canvas', None):
            config['canvas'] = document.getElementById(config['canvas_id'])

        self.app = app
        self.config = config
        self.driver = self.get_driver(driver_names)
        # Fixme: super().__init__(app, config, driver_names)

    def run(self):
        self.animate(0)

    def animate(self, delta):
        self.app.render(self)
        window.requestAnimationFrame(self.animate)

    def get_driver(self, driver_names):
        """Hack to fix because of a brython bug,
        it will be fixed in version 3.2.8
        """
        return webgl.driver(self.config)
