from typing import Any, Dict, List
import torusgrid as tg
from pathlib import Path
import json
import os


class Fallback(Dict[str, Any]):
    """
    A dictionary with fallback values
    """
    def __init__(
        self, 
        data: Dict[str, Any],
        fallback: Dict[str, Any],
        fallback_keys: List[str]
    ):
        self._fallback = fallback
        self.update(data)
        self._fallback_keys = fallback_keys

    def __getitem__(self, key):
        if key in self.keys():
            return super().__getitem__(key)

        if key in self._fallback_keys:
            if key in self._fallback.keys():
                return self._fallback[key]

        raise KeyError(f'{key}')


def put_val(d: Dict[str,Any], *keys: str, val: Any):
    """
    Put a value inside a dict at arbitrary depth
    """
    node = d
    for key in keys[:-1]:
        node[key] = {} if key not in node.keys() else node[key]
        node = node[key]

    node[keys[-1]] = val


def has_key(d: Dict[str,Any], *keys: str):
    node = d
    for key in keys:
        if key not in node.keys():
            return False
        node = node[key]
    return True



def put_val_into_json(
    path: str, *keys: str, val: Any,
    create_file: bool = True
):
    
    if (not Path(path).exists()) and create_file:
        with open(path, 'w') as f:
            json.dump(dict(), f, indent=4)


    with open(path, 'r') as f:
        data: dict = json.load(f)

    put_val(data, *keys, val=val)

    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def json_has_key(
    path: str, *keys: str,
    allow_absent: bool = True
):
    if not Path(path).exists():
        if allow_absent:
            return False
        else:
            raise FileNotFoundError(path)

    with open(path, 'r') as f:
        data = json.load(f)
    
    return has_key(data, *keys)



class FieldLoader:

    def __init__(self, path) -> None:
        self.path = path

    def __call__(self):
        return tg.load(tg.RealField2D, self.path)


def get_interface_list(path: str):

    dir = Path(path)
    
    if dir.exists():
        if dir.is_dir():
            ifcs = sorted([str(p) for p in list(dir.glob('*.field'))])
        else:
            raise NotADirectoryError(str(dir))
    else:
        ifcs = []

    return [FieldLoader(p) for p in ifcs]



class DataExistsError(Exception): ...



def check_dir_empty(
    path: str, *, 
    overwrite: bool,
    absent_okay: bool = True
):

    pth = Path(path)

    if pth.exists():
        if not pth.is_dir():
            raise NotADirectoryError(f'Saving location {path} is not a directory')

        files = os.listdir(str(path))
        if not (files == []):
            if (not overwrite):
                raise DataExistsError(f'Saving directory {path} not empty')
    else:
        if not absent_okay:
            raise FileNotFoundError(path)


