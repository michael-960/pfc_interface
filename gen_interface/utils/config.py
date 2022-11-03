from __future__ import annotations
from typing import List
import yaml
import torusgrid as tg
import pfc_util as pfc
import pickle

class BaseConfig:
    def __init__(self, parent: InterfaceGenConfig, config: dict):

        self.n_steps = int(config['n_steps'])
        self.target = str(config['target'])
        self.tol = parent.dtype(config['tol'])
        self.patience = int(config['patience'])
        self.refresh_interval = int(config['refresh_interval'])

        self.fft_threads = int(config['fft_threads'])
        self.wisdom_only = bool(config['wisdom_only'])

class LongConfig:
    def __init__(self, parent: InterfaceGenConfig, config: dict) -> None:

        self.mx = int(config['mx'])
        self.my = int(config['my'])
        self.width0 = parent.dtype(config['width0'])

        self.n_steps = int(config['n_steps'])
        self.target = str(config['target'])
        self.tol = parent.dtype(config['tol'])
        self.patience = int(config['patience'])
        self.refresh_interval = int(config['refresh_interval'])

        self.fft_threads = int(config['fft_threads'])
        self.wisdom_only = bool(config['wisdom_only'])



class InterfaceGenConfig:
    def __init__(self, config: dict):

        self.precision = tg.FloatingPointPrecision.cast(config['precision'])
        self.dtype = tg.get_real_dtype(config['precision'])


        self.eps = self.dtype(config['eps'])
        self.alpha = self.dtype(config['alpha'])
        self.beta= self.dtype(config['beta'])

        self.nx = int(config['nx'])
        self.ny = int(config['ny'])

        self.na = int(config['na'])
        self.nb = int(config['nb'])

        self.rotator = pfc.toolkit.UnitCellRotator(self.na, self.nb)

        self.theta = self.rotator.theta

        self.dt = self.dtype(config['dt'])

        self.fps = int(config['fps'])

        self.base = BaseConfig(self, config['base'])
        self.long = LongConfig(self, config['long'])
        
        self.file_prefix = f'{self.nx}x{self.ny}/eps_{config["eps"]}/alpha_{config["alpha"]}/beta_{config["beta"]}'

        self.file_prefix_with_angle = f'{self.file_prefix}/theta_{self.theta:.4f}'

        self.fftw_wisdoms = []
        for wisdom_file in config['fftw_wisdoms']:
            with open(wisdom_file, 'rb') as f:
                wisdom = pickle.load(f)
            self.fftw_wisdoms.append(wisdom)


        with open(f'./data/{self.file_prefix}/log.pkl', 'rb') as f:
            self.log: List[pfc.toolkit.MuSearchRecord] = pickle.load(f)

        self.mu = self.log[-1].mu[-1]


def parse_config(fname: str='./config.yaml') -> InterfaceGenConfig:

    with open(fname, 'r') as f:
        config = yaml.safe_load(f)

    
    return InterfaceGenConfig(config)
