from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import torusgrid as tg
import pfc_util as pfc
import pickle


class IHasToFloat(ABC):

    @abstractmethod
    def to_float(self, x: str) -> tg.FloatLike: ...


class ConfigBase:
    def __init__(self, config: dict):
        ...


class SpecifiesShape(ConfigBase):
    """
    nx, ny
    """

    def __init__(self, config: dict):
        super().__init__(config)

        self.nx = int(config['nx'])
        self.ny = int(config['ny'])


class SpecifiesFFTWisdoms(ConfigBase):
    """
    fftw_wisdoms
    """
    def __init__(self, config: dict):
        super().__init__(config)
        self.fftw_wisdoms = []
        for wisdom_file in config['fftw_wisdoms']:
            with open(wisdom_file, 'rb') as f:
                wisdom = pickle.load(f)
            self.fftw_wisdoms.append(wisdom)


class SpecifiesPFCParams(ConfigBase):
    """
    eps, alpha, beta (strings)
    """
    def __init__(self, config: dict):
        super().__init__(config)
        self.eps = str(config['eps'])
        self.alpha= str(config['alpha'])
        self.beta = str(config['beta'])


class SpecifiesRotationAngle(ConfigBase):
    """
    na, nb

    rotator, theta
    """
    def __init__(self, config: dict):
        super().__init__(config)
        self.na = int(config['na'])
        self.nb = int(config['nb'])
        self.rotator = pfc.toolkit.UnitCellRotator(self.na, self.nb)
        self.theta = self.rotator.theta


class SpecifiesPrecision(ConfigBase, IHasToFloat):
    """
    precision, dtype
    """
    def __init__(self, config: dict):
        super().__init__(config)
        self.precision = tg.FloatingPointPrecision.cast(config['precision'])
        self.dtype = tg.get_real_dtype(config['precision'])

    def to_float(self, x: str) -> tg.FloatLike:
        return self.dtype(x)


class SpecifiesSimulationParams(ConfigBase, IHasToFloat):
    """
    dt

    target, tol, patience (early stopping)

    n_steps, refresh_interval, fps (display)

    fft_threads, wisdom_only (FFT)
    """
    def __init__(self, config: dict):
        super().__init__(config)

        self.dt = self.to_float(config['dt'])

        self.target = str(config['target'])

        self.tol = self.to_float(config['tol'])

        self.patience = int(config['patience'])

        self.n_steps = int(config['n_steps'])
        self.refresh_interval = int(config['refresh_interval'])
        self.fps = int(config['fps'])

        self.fft_threads = int(config['fft_threads'])
        self.wisdom_only = bool(config['wisdom_only'])



