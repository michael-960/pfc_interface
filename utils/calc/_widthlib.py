from typing import Tuple


import numpy as np
from scipy.fft import fft2, ifft2
from scipy.optimize import curve_fit

import torusgrid as tg


def _sigmoid(x, b):
    return .5 * (1. + np.tanh((b*x)/2))


def get_rotated_unit_cell(
        field: tg.RealField2D, theta: tg.FloatLike, *, 
        uc_stretch_factor: tg.FloatLike= 1.
        ) -> np.ndarray:
    '''
        Return a field with the same dimensions as input, but with one region
        corresponding to a unit cell set to 1, while the remaining area is 0.
    '''
    mirror_matrix = [(0, 1), (0, 0), (0, -1), (0, -2), (-1, 1), (-1, 0), (-1, -1), (-1, -2)]

    X_cloned = np.array([field.x + p[0]*field.lx for p in mirror_matrix])
    Y_cloned = np.array([field.y + p[1]*field.ly for p in mirror_matrix])

    # rotation
    X0 = np.cos(theta)*X_cloned - np.sin(theta)*Y_cloned
    Y0 = np.sin(theta)*X_cloned + np.cos(theta)*Y_cloned 

    
    b = 1/field.dx * 20
    WEIGHTS = (_sigmoid(4*np.pi*uc_stretch_factor-X0, b) * 
               _sigmoid(X0, b) * _sigmoid(4*np.pi/np.sqrt(3)*uc_stretch_factor-Y0, b) * 
               _sigmoid(Y0, b))

    unit_cell = np.sum(WEIGHTS, axis=(0,))
    return unit_cell


def hexagonal_amplitudes(
        field: tg.RealField2D, 
        unit_cell: np.ndarray, 
        theta: tg.FloatLike, *,
        uc_strech_factor: tg.FloatLike= 1.
        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Calculate the amplitudes of principal RLVs of the hexagonal lattice of the
    given 2D function.

    Return: 3 complex 2D ndarrays
    '''
    # calculate amplitude
    
    # number of points in a unit cell
    num_points_uc = np.sum(unit_cell)

    k0 = 1 / uc_strech_factor
    k1_x, k1_y = k0*np.cos(-theta), k0*np.sin(-theta)
    k2_x, k2_y = k0*np.cos(-theta+2*np.pi/3), k0*np.sin(-theta+2*np.pi/3)
    k3_x, k3_y = k0*np.cos(-theta+4*np.pi/3), k0*np.sin(-theta+4*np.pi/3)

    # plane waves filtered with unit cell
    H1: np.ndarray = np.exp(1j* (k1_x*field.x + k1_y*field.y)) * unit_cell
    H1_k = fft2(H1)

    H2 = np.exp(1j* (k2_x*field.x + k2_y*field.y)) * unit_cell
    H2_k = fft2(H2)

    H3 = np.exp(1j* (k3_x*field.x + k3_y*field.y)) * unit_cell
    H3_k = fft2(H3)

    psi_k = fft2(field.psi)

    # amplitudes
    A1 = np.exp(-1j*(k1_x*field.x + k1_y*field.y)) * ifft2(H1_k * psi_k) / num_points_uc # type: ignore
    A2 = np.exp(-1j*(k2_x*field.x + k2_y*field.y)) * ifft2(H2_k * psi_k) / num_points_uc # type: ignore
    A3 = np.exp(-1j*(k3_x*field.x + k3_y*field.y)) * ifft2(H3_k * psi_k) / num_points_uc # type: ignore

    return A1, A2, A3


def test_tanh(x, w, a, A0):
    return (np.tanh((x-a)/w) + 1) * A0 / 2


class TanhParams:
    def __init__(self, w: tg.FloatLike, a: tg.FloatLike, A0: tg.FloatLike):
        self._w = w
        self._a = a
        self._A0 = A0

    @property
    def width(self): return self._w

    @property
    def shift(self): return self._a

    @property
    def magnitude(self): return self._A0


def fit_tanh(
        x: np.ndarray, y: np.ndarray, *,
        width0: tg.FloatLike = 10.0, 
        shift0: tg.FloatLike = 0., 
        amp0: tg.FloatLike = 0.05
    ) -> TanhParams:

    param, _ = curve_fit(test_tanh, x, y, p0=[width0, shift0, amp0])
    return TanhParams(*param)


def calculate_widths(
        field: tg.RealField2D,
        theta: tg.FloatLike, *,
        uc_factor: tg.FloatLike = 1.,
        ):
    # rotated unit cell
    rotated_uc = get_rotated_unit_cell(
            field, 
            theta, uc_stretch_factor=uc_factor)

    A1, A2, A3 = hexagonal_amplitudes(
            field, 
            rotated_uc, theta, 
            uc_strech_factor=uc_factor)


    # extract x-dependence

    Nx = field.nx

    B1 = np.abs(np.mean(A1, axis=(1,)))
    B2 = np.abs(np.mean(A2, axis=(1,)))
    B3 = np.abs(np.mean(A3, axis=(1,)))

    x = field.x[:,0]


    tanh1 = fit_tanh(
            x[:Nx//2], B1[:Nx//2], 
            width0=18, shift0=field.lx/4, amp0=.05)

    tanh2 = fit_tanh(
            x[:Nx//2], B2[:Nx//2], 
            width0=18, shift0=field.lx/4, amp0=.05)

    tanh3 = fit_tanh(
            x[:Nx//2], B3[:Nx//2], 
            width0=18, shift0=field.lx/4, amp0=.05)

    return tanh1.width, tanh2.width, tanh3.width


