from vulk.container.basecontainer import BaseContainer


class WebContainer(BaseContainer):
    """Launch app on web
    """

    def __init__(self, app, user_config=None, driver_names=("webgl2")):
        config = {
            'canvas_id': 'app_canvas'
        }
        config.update(user_config if user_config else {})
        super().__init__(app, config, driver_names)
