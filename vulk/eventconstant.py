import enum
import sdl2


class EventType(enum.IntEnum):
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
    WINDOW = sdl2.SDL_WINDOWEVENT


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


class MouseMotionEvent(BaseEvent):
    def __init__(self, event):
        '''Create mouse motion event from `event`

        *Parameters:*

        - `event`: `SDL_MouseMotionEvent`
        '''
        super().__init__(event)
        self.x = event.motion.x
        self.y = event.motion.y


class QuitEvent(BaseEvent):
    def __init__(self, event):
        '''Create quit event from `event`

        *Parameters:*

        - `event`: `SDL_QuitEvent`
        '''
        super().__init__(event)


map_sdl_vulk = {
    EventType.KEY_UP: KeyboardEvent,
    EventType.KEY_DOWN: KeyboardEvent,
    EventType.MOUSE_MOTION: MouseMotionEvent,
    EventType.QUIT: QuitEvent
}


def to_vulk_event(event):
    '''Convert a SDL2 event to a Vulk Event

    *Parameters:*

    - `event` : `SDL_Event`
    '''
    vulk_class = map_sdl_vulk.get(event.type)
    return vulk_class(event) if vulk_class else None
