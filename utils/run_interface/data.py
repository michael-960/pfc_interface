import os
from pathlib import Path
import torusgrid as tg


def loader(path: str):
    def load():
        return tg.load(tg.RealField2D, path)
    return load


def get_interface_list(path: str):

    dir = Path(path)
    
    if dir.exists():
        if dir.is_dir():
            ifcs = sorted([str(p) for p in list(dir.glob('*.field'))])
        else:
            raise NotADirectoryError(str(dir))
    else:
        ifcs = []



    return [loader(p) for p in ifcs]


