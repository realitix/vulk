'''Audio module

This module contains all audio related classes.
'''
import logging
import sdl2
from sdl2 import sdlmixer as mixer
from sdl2.ext.compat import byteify

from vulk.exception import SDL2Error, SoundError


logger = logging.getLogger()


class VulkAudio():
    '''This class is only used in baseapp.

    It initializes and close the audio system.
    '''
    def open(self, configuration):
        '''Open and configure audio system

        *Parameters:*

        - `configuration`: Configuration parameters from Application
        '''
        if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO) != 0:
            msg = "Cannot initialize audio system: %s" % sdl2.SDL_GetError()
            logger.critical(msg)
            raise SDL2Error(msg)

        if mixer.Mix_OpenAudio(mixer.MIX_DEFAULT_FREQUENCY,
                               mixer.MIX_DEFAULT_FORMAT, 2, 1024):
            msg = "Cannot open mixed audio: %s" % mixer.Mix_GetError()
            logger.critical(msg)
            raise SDL2Error(msg)

        mixer.Mix_AllocateChannels(configuration.audio_channel)

        logger.info("Audio initialized")

    def close(self):
        '''Close the audio system'''
        mixer.Mix_CloseAudio()
        sdl2.SDL_Quit(sdl2.SDL_INIT_AUDIO)
        logger.info("Audio stopped")


class Sound():
    '''
    Sound effects are small audio samples, usually no longer than a few
    seconds, that are played back on specific game events such as a character
    jumping or shooting a gun.

    Sound effects can be stored in various formats. Vulk is based on SDL2 and
    thus supports WAVE, AIFF, RIFF, OGG, and VOC files.
    '''

    def __init__(self, path):
        '''Load the sound file

        *Parameters:*

        - `path`: Path to the sound file
        '''
        self.sample = mixer.Mix_LoadWAV(byteify(path, "utf-8"))

        if not self.sample:
            msg = "Cannot load file %s" % path
            logger.error(msg)
            raise SoundError(msg)

    def play(self, volume=1.0, repeat=1):
        '''
        Play the sound

        *Parameters:*

        - `volume`: Sound volume 0.0 to 1.0
        - `repeat`: Number of time to repeat the sound, 0=infinity

        *Returns:*

        Channel id of the sound
        '''
        channel = mixer.Mix_PlayChannel(-1, self.sample, repeat-1)
        if channel == -1:
            msg = "Cannot play the sound: %s" % mixer.Mix_GetError()
            logger.error(msg)
            raise SoundError(msg)

        mixer.Mix_Volume(channel, int(mixer.MIX_MAX_VOLUME * volume))
        return channel


class Music():
    '''
    For any sound that's longer than a few seconds it is preferable to stream
    it from disk instead of fully loading it into RAM. Vulk provides a Music
    class that lets you do that.

    Music can be stored in various formats. Vulk is based on SDL2 and
    thus supports WAVE, MOD, MIDI, OGG, MP3, FLAC files.

    **Note: You can play only one music at a time**
    '''

    def __init__(self, path):
        '''Load the music file

        *Parameters:*

        - `path`: Path to the music file
        '''
        self.music = mixer.Mix_LoadMUS(byteify(path, "utf-8"))

        if not self.music:
            msg = "Cannot load file %s" % path
            logger.error(msg)
            raise SoundError(msg)

    def play(self, volume=1.0, repeat=1):
        '''
        Play the music

        *Parameters:*

        - `volume`: Sound volume 0.0 to 1.0
        - `repeat`: Number of time to repeat the sound, 0=infinity

        *Returns:*

        Channel id of the sound
        '''
        if not repeat:
            repeat = -1

        result = mixer.Mix_PlayMusic(self.music, repeat)
        if result == -1:
            msg = "Cannot play the music: %s" % mixer.Mix_GetError()
            logger.error(msg)
            raise SoundError(msg)

        mixer.Mix_VolumeMusic(int(mixer.MIX_MAX_VOLUME * volume))
