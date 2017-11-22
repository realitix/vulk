import sys

from cefpython3 import cefpython as cef
import numpy as np

from vulk import vulkanconstant as vc
from vulk.graphic.d2.batch import SpriteBatch
from vulk.graphic.texture import BinaryTexture


sys.excepthook = cef.ExceptHook
cef.Initialize(settings={"windowless_rendering_enabled": True})


class RenderHandler():
    def __init__(self, context):
        self.context = context
        self.width = 0
        self.height = 0
        self.loaded = False
        self.texture_ready = False
        self.texture = None

    def GetViewRect(self, browser, rect_out):
        print(f"RENDER RESIZE: {self.width} {self.height}")
        self.texture = BinaryTexture(self.context, self.width, self.height,
                                     vc.Format.R8G8B8A8_UNORM, None)
        rect_out.extend([0, 0, self.width, self.height])
        return True

    def OnPaint(self, browser, element_type, dirty_rects, paint_buffer,
                width, height):
        if self.texture.width != width or self.texture.height != height:
            return

        if self.loaded:
            self.texture.bitmap = np.frombuffer(
                paint_buffer.GetString(mode="rgba", origin="top-left"),
                dtype=np.uint8
            )
            self.texture.upload_buffer(self.context, 0)
            self.texture.upload(self.context)
            self.texture_ready = True
            print(paint_buffer)

    def OnLoadingStateChange(self, browser, is_loading, **_):
        """Called when the loading state has changed."""
        if not is_loading:
            self.loaded = True
            print("[screenshot.py] Web page loading is complete")


class Ui():
    def __init__(self, context, html_file):
        self.html_file = html_file
        self.batch = SpriteBatch(context)
        self.handler = RenderHandler(context)
        self.browser = self._create_browser()
        self.resize(context)

    def _create_browser(self):
        parent_window_handle = 0
        window_info = cef.WindowInfo()
        window_info.SetAsOffscreen(parent_window_handle)
        window_info.SetTransparentPainting(True)
        browser = cef.CreateBrowserSync(window_info=window_info,
                                        url="http://google.fr")
        browser.SetClientHandler(self.handler)
        browser.SendFocusEvent(True)
        return browser

    def resize(self, context):
        print("resize: {}, {}", context.width, context.height)
        self.handler.width = context.width
        self.handler.height = context.height
        self.batch.reload(context)
        self.browser.WasResized()

    def render(self, context):
        cef.MessageLoopWork()
        if self.handler.texture_ready:
            self.batch.begin(context)
            self.batch.draw(self.handler.texture, 0, 0)
            return self.batch.end()
        return []
