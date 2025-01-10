def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def file_exists(f):
    import os
    if f in os.listdir():
        return True
    else:
        return False


def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min