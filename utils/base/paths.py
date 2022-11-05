from __future__ import annotations
from typing import Optional, overload
import pfc_util as pfc


@overload
def get_path(nx: int, ny: int) -> str: ...

@overload
def get_path(
    nx: int, ny: int, 
    eps: str, alpha: str, beta: str
) -> str:...

@overload
def get_path(
    nx: int, ny: int,
    eps: str, alpha: str, beta: str,
    na: int, nb: int
) -> str: ...

def get_path(
    nx: int, ny: int,
    eps: Optional[str] = None,
    alpha: Optional[str] = None,
    beta: Optional[str] = None,
    na: Optional[int] = None,
    nb: Optional[int] = None,
    ) -> str:
   
    s = f'{nx}x{ny}' 

    if eps is not None:
        s += f'/eps_{eps}/alpha_{alpha}/beta_{beta}'

    if na is not None:
        assert nb is not None
        theta = pfc.toolkit.UnitCellRotator(na, nb).theta
        s += f'/theta_{theta:.4f}'

    return s


