from path import Path

from vulk.graphic.texture import Texture, TextureRegion
from vulk.graphic.d2.batch import CharBatch


class FontData():
    """Load a BMFont Text file into a FontData

    The FontData can be rendered with the CharBatch.
    See http://www.angelcode.com/products/bmfont/doc/file_format.html
    """
    def __init__(self, context, filepath):
        self.filepath = Path(filepath)
        self.raw_data = FontData.load_bmfont(filepath)
        self.pages = self._init_pages(context)
        self.regions = self._init_regions()
        self.chars = self._init_chars()

    def _init_pages(self, context):
        """Create Texture for each page

        Args:
            context (VulkContext): Vulk context

        Returns:
            Page indexed dict
        """
        res = {}
        dirpath = self.filepath.parent
        for p in self.raw_data['page']:
            res[p['id']] = Texture(context, dirpath / p['file'])

        return res

    def _init_regions(self):
        """Create a TextureRegion for each char

        Returns:
            Char indexed dict
        """
        res = {}
        for c in self.raw_data['char']:
            k = chr(c['id'])
            t = self.pages[c['page']]
            x = c['x']
            y = c['y']
            w = c['width']
            h = c['height']
            res[k] = TextureRegion.from_pixels(t, x, y, w, h)

        return res

    def _init_chars(self):
        """Create dict indexed key for each char

        Returns:
            Char indexed dict
        """
        res = {}
        for c in self.raw_data['char']:
            k = chr(c['id'])
            res[k] = c

        return res

    def get_region(self, char):
        """Get texture region of char in this FontData

        Args:
            char (str): One character to find
        """
        return self.regions[char]

    def get_sizes(self, char):
        """Get size of char in this FontData

        Args:
            char (str): One character to find
        """
        return (self.chars[char]['width'], self.chars[char]['height'])

    @staticmethod
    def load_bmfont(filepath):
        """Convert the BMFont file into a dict

        Args:
            filename (str): BMFont file
        """
        def extract(attributes):
            result = {}
            for attrib in attributes:
                key, value = attrib.split("=")
                try:
                    result[key] = int(value)
                except ValueError:
                    strval = value.strip('"')
                    if ',' in strval:
                        arry = strval.split(',')
                        try:
                            arry = map(int, arry)
                        finally:
                            result[key] = arry
                    else:
                        result[key] = strval
            return result

        with open(filepath) as f:
            lines = f.readlines()

        atlas = {}
        for line in lines:
            attributes = [x for x in line.split()]
            k = attributes[0]
            res = extract(attributes[1:])
            if k in ("char", "page", "kerning"):
                if not atlas.get(k):
                    atlas[k] = []
                atlas[k].append(res)
            else:
                atlas[k] = res

        return atlas


class TextRenderer():
    """TextRenderer performs computation to draw text"""
    def __init__(self, context, fontdata, batch=None):
        """Initialize TextRenderer

        Args:
            context (VulkContext): Context
            fontdata (FontData): Font to use
            batch: Batch with `draw_char` function
        """
        if not batch:
            batch = CharBatch(context)

        self.fontdata = fontdata
        self.batch = batch

    def begin(self, context):
        """Start rendering

        Args:
            context (VulkContext): Context
        """
        self.batch.begin(context)

    def end(self):
        """Stop rendering

        Returns:
            Semaphore signaled when all drawing operations are finished
        """
        return self.batch.end()

    def draw(self, text, x, y, size, r=1., g=1., b=1., a=1., rotation=0.):
        """Render text on screen

        Args:
            text (str): String to render
            x (int): X position (from left)
            y (int): Y position (from top)
            size (float): Pixel size of font
            r (float): Red channel
            g (float): Green channel
            b (float): Blue channel
            a (float): Alpha channel
            rotation (float): Rotation in radian (clockwise)
        """
        current_x = x
        current_y = y
        scale = size / self.fontdata.raw_data['info']['size']

        for char in text:
            char_info = self.fontdata.chars[char]
            x = current_x + char_info['xoffset']
            y = current_y + char_info['yoffset']
            self.batch.draw_char(self.fontdata, char, x, y, r, g, b, a, scale,
                                 scale, rotation)
            current_x += char_info['xadvance']
