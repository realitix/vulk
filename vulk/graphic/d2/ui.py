from cefpython3 import cefpython as cef


class UI():
    def __init__(self, html):
        self.html = html
        cef.Initialize(settings={"windowless_rendering_enabled": True})

    def _create_browser():
        parent_window_handle = 0
        window_info = cef.WindowInfo()
        window_info.SetAsOffscreen(parent_window_handle)
        browser = cef.CreateBrowserSync(window_info=window_info,

