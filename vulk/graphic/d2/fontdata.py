from path import Path

from vulk.graphic.texture import Texture, TextureRegion


class FontData():
    """Load a BMFont Text file into a FontData

    The FontData can be rendered with the TextBatch.
    See http://www.angelcode.com/products/bmfont/doc/file_format.html
    """
    def __init__(self, context, filepath):
        self.filepath = Path(filepath)
        self.raw_data = FontData.load_bmfont(filepath)
        self.pages = self._init_pages(context)
        self.regions = self._init_regions()
        self.sizes = self._init_sizes()

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

    def _init_sizes(self):
        """Create dimensions for each char

        Returns:
            Char indexed dict
        """
        res = {}
        for c in self.raw_data['char']:
            k = chr(c['id'])
            res[k] = (c['width'], c['height'])

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
        return self.sizes[char]

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
