# pylint: disable=unused-argument
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
    When an event is sent to the `EventChain`, included event listeners
    will intercept events until one of them return False.
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


class DispatchEventListener(RawEventListener):
    '''
    This class dispatch each event to its specific function.
    This class is very basic and performs no logic.
    To get more logic, you must use `BaseEventListener`.
    '''
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
            return self.mouse_move(e.x, e.y, e.xr, e.yr)
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

    def mouse_move(self, x, y, xr, yr):
        '''Called when mouse is moving

        *Parameters:*

        - `x`: X position in Screen coordinate
        - `y`: Y position in Screen coordinate
        - `xr`: X relative position since the last move
        - `yr`: Y relative position since the last move
        '''
        return False

    def quit(self):
        '''Called when App must quit'''
        return False


class BaseEventListener(DispatchEventListener):
    '''Extends `DispatchEventListener` with smarter functions'''

    def __init__(self):
        self.mouse_clicked = -1

    def mouse_down(self, x, y, button):
        self.mouse_clicked = button
        return False

    def mouse_up(self, x, y, button):
        self.mouse_clicked = -1
        return False

    def mouse_move(self, x, y, xr, yr):
        if self.mouse_clicked != -1:
            return self.mouse_drag(x, y, xr, yr, self.mouse_clicked)
        return False

    def mouse_drag(self, x, y, xr, yr, button):
        '''Called when mouse is dragged

        *Parameters:*

        - `x`: X position in Screen coordinate
        - `y`: Y position in Screen coordinate
        - `xr`: X relative position since the last move
        - `yr`: Y relative position since the last move
        - `button`: `vulk.input.Button`
        '''
        return False


def wrap_callback(f):
    '''
    Decorator used in `CallbackEventListener`.
    If a callback exists for the event, we call the callback, else we
    return False.
    '''
    def wrapper(self, *args):
        getattr(BaseEventListener, f.__name__)(self, *args)
        cb = getattr(self, f.__name__ + '_callback')
        if cb:
            return cb(*args)
        return False
    return wrapper


class CallbackEventListener(BaseEventListener):
    '''
    Like `BaseEventListener` but with callback.
    You must pass named parameters with the exact same name as in
    `BaseEventListener`.

    *Example:*

    ```
    listener = CallbackEventListener(key_up=callback1, key_down=callback2)
    ```
    '''

    def __init__(self, key_down=None, key_up=None, mouse_down=None,
                 mouse_drag=None, mouse_move=None, mouse_up=None,
                 quit=None):  # pylint: disable=redefined-builtin
        # We use a custom dict instead of locals() to avoid black magic
        parameters = {
            'key_down': key_down,
            'key_up': key_up,
            'mouse_down': mouse_down,
            'mouse_drag': mouse_drag,
            'mouse_move': mouse_move,
            'mouse_up': mouse_up,
            'quit': quit
        }
        for key, value in parameters.items():
            setattr(self, key + '_callback', value)
        super().__init__()

    @wrap_callback
    def key_down(self, *args):
        pass

    @wrap_callback
    def key_up(self, *args):
        pass

    @wrap_callback
    def mouse_drag(self, *args):
        pass

    @wrap_callback
    def mouse_move(self, *args):
        pass

    @wrap_callback
    def quit(self, *args):
        pass
