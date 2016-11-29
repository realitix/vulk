import time


def millis():
    '''Return the time in milliseconds'''
    return time.perf_counter() * 1000


def time_since_millis(previous_time):
    '''Return the time in millisecons from the previous_time argument'''
    return millis() - previous_time
