# loads a BMFont Text format glyph atlas into a dictionary
# see https://71squared.com/blog/bitmap-font-file-format for more info


def load_glyph_atlas(filename):
    atlas = {}
    for line in open(filename):
        attributes = line.split(" ")
        attributes = [x for x in attributes if x != '' and x != '\n']
        dictkey = attributes[0]
        if dictkey in atlas:
            attribdict = atlas[dictkey]
        else:
            attribdict = atlas[dictkey] = {}
        if dictkey in ['char', 'page']:
            c = int(attributes[1].split("=")[1])
            entry = {}
            for attrib in attributes[2:]:
                key, value = attrib.split("=")
                try:
                    entry[key] = float(value)
                except:
                    entry[key] = value.strip('\"\n')
                attribdict[c] = entry
        else:
            for attrib in attributes[1:]:
                key, value = attrib.split("=")
                try:
                    attribdict[key] = float(value)
                except ValueError:
                    strval = value.strip('\"\n')
                    if ',' in strval:
                        arry = strval.split(',')
                        try:
                            arry = map(float, arry)
                        finally:
                            attribdict[key] = arry
                    else:
                        attribdict[key] = strval
    return atlas
