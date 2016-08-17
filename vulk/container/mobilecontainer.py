from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from vulk.container.basecontainer import BaseContainer


class MobileContainer(BaseContainer):
    """Launch app on mobile
    """

    def __init__(self, app, user_config=None,
                 driver_names=("opengles3")):
        config = {
            'title': 'Vulk'
        }
        config.update(user_config if user_config else {})
        super().__init__(app, config, driver_names)

    def run(self):
        KivyApp(self.app(self.driver)).run()


class KivyApp(App):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.vulk_renderer = VulkRenderer(app)

    def build(self):
        return self.vulk_renderer


class VulkRenderer(Widget):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        Clock.schedule_interval(self.animate, 1 / 60)

    def animate(self, delta):
        self.app.render(delta)
