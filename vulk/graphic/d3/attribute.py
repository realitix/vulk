'''
This package contains material and attributes class
'''


# ----------
# Attributes
# ----------
class Attributes():
    '''Attributes is the base class for all attributes container.
    `Environment` and `Material` are attribute container
    '''

    def __init__(self, attributes=None):
        '''
        *Parameters:*

        - `attributes`: `list` of attributes ot initialize this object
        '''
        self.attributes = {}

        if attributes:
            for a in attributes:
                self.set(a)

    def set(self, attribute):
        '''Set a material attribute

        *Parameters:*

        - `attribute`: `Attribute` to set
        '''
        self.attributes[attribute.__class__] = attribute

    def get(self, attribute_class):
        '''Get an attribute by class

        *Parameters:*

        - `attribute_class`: Class of the attribute to retrieve
        '''
        return self.attributes[attribute_class]


class Material(Attributes):
    '''Material is a container for `Attribute` objects

    Only one object of the same `Attribute` class can be inside the
    material. If you set an attribute which is already in the `Material`,
    the old one is replaced by the new one.
    '''
    pass


class Environments(Attributes):
    '''
    Environment contains all `Attribute` related to the environment,
    like lights, fogs...
    '''
    pass


# ----------
# Attribute
# ----------
class Attribute():
    '''
    Base class for attribute classes.
    '''

    def __init__(self, value):
        self.value = value


class ColorAttribute(Attribute):
    pass
