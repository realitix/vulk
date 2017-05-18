from path import Path
from math import cos, sin

from vulk.graphic.texture import HighQualityTexture, TextureRegion
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
        self.kernings = self._init_kernings()
        self.base = int(self.raw_data['common']['base'])

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
            res[p['id']] = HighQualityTexture(context, dirpath / p['file'])

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

    def _init_kernings(self):
        """Create tuple(char1, char2) indexed key for each kerning

        Returns:
            tuple indexed dict
        """
        res = {}
        for k in self.raw_data['kerning']:
            c1 = chr(k['first'])
            c2 = chr(k['second'])
            res[(c1, c2)] = k['amount']

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

    def get_kerning(self, previous_char, current_char):
        """Get kerning between last and current char

        Args:
            previous_char (str): Previous character
            current_char (str): Current character
        """
        try:
            x = self.kernings[(previous_char, current_char)]
        except KeyError:
            x = 0

        return x

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
    def __init__(self, context, batch=None):
        """Initialize TextRenderer

        Args:
            context (VulkContext): Context
            batch: Batch with `draw_char` function
        """
        if not batch:
            batch = CharBatch(context)

        self.batch = batch

    def begin(self, context, semaphores=None):
        """Start rendering

        Args:
            context (VulkContext): Context
            semaphores (list): Semaphore list
        """
        self.batch.begin(context, semaphores=semaphores)

    def end(self):
        """Stop rendering

        Returns:
            Semaphore signaled when all drawing operations are finished
        """
        return self.batch.end()

    def draw(self, fontdata, text, x, y, size, r=1., g=1., b=1., a=1.,
             rotation=0.):
        """Render text on screen

        Args:
            fontdata (FontData): Font to render
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
        x_abs = x
        y_abs = y
        x_current = 0
        y_current = 0
        scale = size / fontdata.raw_data['info']['size']
        previous_char = None

        for char in text:
            # Compute kerning
            kerning = 0
            if previous_char is not None:
                kerning = fontdata.get_kerning(previous_char, char)

            # Compute position
            char_info = fontdata.chars[char]
            x = x_current + (char_info['xoffset'] + kerning) * scale
            y = y_current + char_info['yoffset'] * scale

            # Compute rotation
            t = rotation
            x2 = x * cos(t) - y * sin(t)
            y2 = x * sin(t) + y * cos(t)

            # Add absolution position
            x2 += x_abs
            y2 += y_abs

            # Draw char
            # TODO: rotation is not properly handled
            # Rotation is done at char center, we should add offset
            # to take rotation into account
            # I don't have time to do the math work right now
            self.batch.draw_char(fontdata, char, x2, y2, r, g, b, a,
                                 scale, scale, t)

            # Register variable
            x_current += char_info['xadvance'] * scale
            previous_char = char
