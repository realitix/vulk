from enum import IntEnum
import sdl2


class Button(IntEnum):
    LEFT = sdl2.SDL_BUTTON_LEFT
    MIDDLE = sdl2.SDL_BUTTON_MIDDLE
    RIGHT = sdl2.SDL_BUTTON_RIGHT
    X1 = sdl2.SDL_BUTTON_X1
    X2 = sdl2.SDL_BUTTON_X2


class EventType(IntEnum):
    AUDIO_DEVICE_ADDED = sdl2.SDL_AUDIODEVICEADDED
    AUDIO_DEVICE_REMOVED = sdl2.SDL_AUDIODEVICEREMOVED
    CONTROLLER_AXIS_MOTION = sdl2.SDL_CONTROLLERAXISMOTION
    CONTROLLER_BUTTON_DOWN = sdl2.SDL_CONTROLLERBUTTONDOWN
    CONTROLLER_BUTTON_UP = sdl2.SDL_CONTROLLERBUTTONUP
    CONTROLLER_DEVICE_ADDED = sdl2.SDL_CONTROLLERDEVICEADDED
    CONTROLLER_DEVICE_REMOVED = sdl2.SDL_CONTROLLERDEVICEREMOVED
    CONTROLLER_DEVICE_REMAPPED = sdl2.SDL_CONTROLLERDEVICEREMAPPED
    # No dollar gesture: logic implemented in Vulk
    DROP_FILE = sdl2.SDL_DROPFILE
    DROP_TEXT = sdl2.SDL_DROPTEXT
    DROP_BEGIN = sdl2.SDL_DROPBEGIN
    DROP_COMPLETE = sdl2.SDL_DROPCOMPLETE
    FINGER_MOTION = sdl2.SDL_FINGERMOTION
    FINGER_DOWN = sdl2.SDL_FINGERDOWN
    FINGER_UP = sdl2.SDL_FINGERUP
    KEY_DOWN = sdl2.SDL_KEYDOWN
    KEY_UP = sdl2.SDL_KEYUP
    JOY_AXISMOTION = sdl2.SDL_JOYAXISMOTION
    JOY_BALLMOTION = sdl2.SDL_JOYBALLMOTION
    JOY_HATMOTION = sdl2.SDL_JOYHATMOTION
    JOY_BUTTONDOWN = sdl2.SDL_JOYBUTTONDOWN
    JOY_BUTTONUP = sdl2.SDL_JOYBUTTONUP
    JOY_DEVICEADDED = sdl2.SDL_JOYDEVICEADDED
    JOY_DEVICEREMOVED = sdl2.SDL_JOYDEVICEREMOVED
    MOUSE_MOTION = sdl2.SDL_MOUSEMOTION
    MOUSE_BUTTONDOWN = sdl2.SDL_MOUSEBUTTONDOWN
    MOUSE_BUTTONUP = sdl2.SDL_MOUSEBUTTONUP
    MOUSE_WHEEL = sdl2.SDL_MOUSEWHEEL
    QUIT = sdl2.SDL_QUIT
    # We create custom type for window events
    WINDOW = sdl2.SDL_WINDOWEVENT
    WINDOW_RESIZED = sdl2.SDL_WINDOWEVENT_RESIZED


class KeyCode(IntEnum):
    LEFT = sdl2.SDL_SCANCODE_LEFT
    RIGHT = sdl2.SDL_SCANCODE_RIGHT


class BaseEvent():
    def __init__(self, event):
        self.type = event.common.type
        self.timestamp = event.common.timestamp


class KeyboardEvent(BaseEvent):
    def __init__(self, event):
        '''Create keyboard event from `event`

        *Parameters:*

        - `event`: `SDL_KeyboardEvent`
        '''
        super().__init__(event)
        self.key = event.key.keysym.scancode


class MouseButtonEvent(BaseEvent):
    def __init__(self, event):
        '''Create mouse button event from `event`

        *Parameters:*

        - `event`: `SDL_MouseButtonEvent`
        '''
        super().__init__(event)
        self.x = event.motion.x
        self.y = event.motion.y
        self.button = event.button.button


class MouseMotionEvent(BaseEvent):
    def __init__(self, event):
        '''Create mouse motion event from `event`

        *Parameters:*

        - `event`: `SDL_MouseMotionEvent`
        '''
        super().__init__(event)
        self.x = event.motion.x
        self.y = event.motion.y
        self.xr = event.motion.xrel
        self.yr = event.motion.yrel


class QuitEvent(BaseEvent):
    pass


class WindowEvent():
    def __init__(self, event):
        self.type = event.window.event
        self.timestamp = event.common.timestamp


class WindowResizedEvent(WindowEvent):
    def __init__(self, event):
        """Create window resized event from `event`

        Args:
            event (SDL_WindowEvent)
        """
        super().__init__(event)
        self.width = event.window.data1
        self.height = event.window.data2


def window_event_builder(event):
    """Create widow event according to event"""
    if event.window.event == EventType.WINDOW_RESIZED:
        return WindowResizedEvent(event)


map_sdl_vulk = {
    EventType.KEY_UP: KeyboardEvent,
    EventType.KEY_DOWN: KeyboardEvent,
    EventType.MOUSE_BUTTONUP: MouseButtonEvent,
    EventType.MOUSE_BUTTONDOWN: MouseButtonEvent,
    EventType.MOUSE_MOTION: MouseMotionEvent,
    EventType.QUIT: QuitEvent,
    EventType.WINDOW: window_event_builder
}


def to_vulk_event(event):
    '''Convert a SDL2 event to a Vulk Event

    *Parameters:*

    - `event` : `SDL_Event`
    '''
    vulk_class = map_sdl_vulk.get(event.type)
    return vulk_class(event) if vulk_class else None
