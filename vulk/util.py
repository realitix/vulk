import time


def millis():
    """Return the time in milliseconds"""
    return time.perf_counter() * 1000


def nanos():
    """Return the time in nanoseconds"""
    return millis() * 1000000


def time_since_millis(previous_time):
    """Return the time in milliseconds from the previous_time argument"""
    return millis() - previous_time


def mipmap_size(base_width, base_height, mip_level):
    """Return mipmap width and height

    Args:
        base_width (int): Width of the base image (mip level 0)
        base_height (int): Height of the base image (mip level 0)
        mip_level (int): Level of mip to get

    Returns:
        tuple(mip_width, mip_height)
    """
    width = base_width
    height = base_height

    for _ in range(mip_level):
        width = width // 2 or 1
        height = height // 2 or 1

    return width, height


def mipmap_levels(base_width, base_height):
    """Return max number of mipmap for the size

    Args:
        base_width (int): Width source
        base_height (int): Height source

    Returns:
        int: Number of mipmap levels
    """
    width = base_width
    height = base_height
    levels = 1

    while width > 1 or height > 1:
        width = width // 2 or 1
        height = height // 2 or 1
        levels += 1

    return levels


def next_multiple(query, multiple):
    """Get the next multiple

    Args:
        query (int): To test
        multiple (int): Divider

    Returns:
        int: Next multiple of divider
    """
    result = query
    while result % multiple:
        result += 1

    return result
