from abc import ABC, abstractmethod
from itertools import takewhile

from vulk import eventconstant as ec


class RawEventListener(ABC):
    '''
    Base class for event listener.
    You shouldn't need to inherit directly from this class,
    it's very low level.
    '''

    @abstractmethod
    def handle(self, event):
        '''Called for each event received

        *Parameters:*

        - `event`: `eventconstant.BaseEvent`

        *Returns:*

        - `True` if event handled
        - `False` otherwise
        '''
        return False


class EventChainListener(RawEventListener):
    '''
    Allow to chain events.
    When an event in sended to the `EventChain`, included event listeners
    will intercept event until one of them return False.
    '''

    def __init__(self, event_listeners=None):
        '''
        *Parameters:*

        - `event_listeners`: `list` of `RawEventListener`
        '''
        self.listeners = []

        if event_listeners:
            self.listeners.extend(event_listeners)

    def handle(self, event):
        '''
        Call event listener until one of them return False.

        *Parameters:*
        '''
        return any(list(takewhile(lambda x: x.handle(event), self.listeners)))


class BaseEventListener(RawEventListener):
    '''This class convert event to specific function.'''
    def handle(self, e):
        '''Called for each event received

        *Parameters:*

        - `e`: `eventconstant.BaseEvent`

        *Returns:*

        - `True` if event handled
        - `False` otherwise
        '''
        # Unknow event
        if not e:
            return False

        if e.type == ec.EventType.KEY_DOWN:
            return self.key_down(e.key)
        elif e.type == ec.EventType.KEY_UP:
            return self.key_up(e.key)
        elif e.type == ec.EventType.MOUSE_BUTTONUP:
            return self.mouse_up(e.x, e.y, e.button)
        elif e.type == ec.EventType.MOUSE_BUTTONDOWN:
            return self.mouse_down(e.x, e.y, e.button)
        elif e.type == ec.EventType.MOUSE_MOTION:
            return self.mouse_move(e.x, e.y)
        elif e.type == ec.EventType.QUIT:
            return self.quit()

        return False

    def key_down(self, keycode):
        '''Called when a key is pressed

        *Parameters:*

        - `keycode`: `vulk.input.KeyCode`
        '''
        return False

    def key_up(self, keycode):
        '''Called when a key is released

        *Parameters:*

        - `keycode`: `vulk.input.KeyCode`
        '''
        return False

    def mouse_down(self, x, y, button):
        '''Called when mouse is released

        *Parameters:*

        - `x`: X position in Screen coordinate
        - `y`: Y position in Screen coordinate
        - `button`: `vulk.input.Button`
        '''
        return False

    def mouse_up(self, x, y, button):
        '''Called when mouse is clicked

        *Parameters:*

        - `x`: X position in Screen coordinate
        - `y`: Y position in Screen coordinate
        - `button`: `vulk.input.Button`
        '''
        return False

    def mouse_move(self, x, y):
        '''Called when mouse is moving

        *Parameters:*

        - `x`: X position in Screen coordinate
        - `y`: Y position in Screen coordinate
        '''
        return False

    def quit(self):
        '''Called when App must quit'''
        return False


class CallbackEventListener(BaseEventListener):
    '''
    Like `BaseEventListener` but with callback.
    Lot of black magic here!
    You must pass named parameters with the exact same name as in
    `BaseEventListener`.

    *Example:*

    ```
    listener = CallbackEventListener(key_up=callback1, key_down=callback2)
    ```
    '''

    def __init__(self, **kwargs):
        '''
        *Parameters:*

        - `key_down`: Callback to call when key down
        - `key_up`: Callback to call when key up
        - `quit`: Callback to call when quit
        '''
        for key, value in kwargs.items():
            setattr(self, key, CallbackEventListener.gen(value))

    @staticmethod
    def gen(callback):
        def f(*args):
            return callback(*args)
        return f
