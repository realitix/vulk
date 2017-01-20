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
        '''Called for each SDL2 event received

        *Parameters:*

        - `event`: `SDL_Event`
        '''
        pass


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
        list(takewhile(lambda x: x.handle(event), self.listeners))


class QuitEventListener(RawEventListener):
    '''
    Listener only listening to quit event.
    When the event arise, the callback function is called.
    '''

    def __init__(self, callback):
        '''
        *Parameters:*

        - `callback`: Callback function to call when Quit event
        '''
        self.callback = callback

    def handle(self, event):
        if event.type == ec.QUIT:
            self.callback()
