from typing import Any, Dict, List


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
