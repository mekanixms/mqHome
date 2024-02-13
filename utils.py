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
