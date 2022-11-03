from __future__ import annotations
from typing import Generic, List, Literal, Type, TypeVar
import numpy as np
import torusgrid as tg
import pfc_util as pfc
import pickle
import yaml


T = TypeVar('T', np.double, np.single, np.longdouble)

class UnitCellSingleRunConfig(Generic[T]):

    def __init__(self, parent: UnitCellSimulationConfig, config: dict):
        self.dtype = tg.get_real_dtype(tg.FloatingPointPrecision.cast(config['precision']))

        self.mu_precision = self.dtype(config['mu_precision'])

        self.dt = self.dtype(config['dt'])

        self.eps = self.dtype(parent.eps)
        self.alpha = self.dtype(parent.alpha)
        self.beta = self.dtype(parent.beta)

        self.tol = self.dtype(config['tol'])

        self.n_steps = int(config['n_steps'])
        self.target = str(config['target'])
        self.patience = int(config['patience'])
        self.fft_threads = int(config['fft_threads'])
        self.refresh_interval = int(config['refresh_interval'])

        self.wisdom_only = bool(config['wisdom_only'])

        self.search_method: Literal['binary', 'interpolate']
        if str(config['search_method']) == 'binary':
            self.search_method = 'binary'
        else:
            self.search_method = 'interpolate'


        self.parent = parent




class UnitCellSimulationConfig:

    def __init__(self, config: dict) -> None:
        self.source = config['source']

        if self.source['type'] == 'static':
            self.source_field = pfc.toolkit.get_relaxed_minimized_coexistent_unit_cell(self.source['name'])
        else:
            self.source_field = tg.load(tg.RealField2D, self.source['name'])

        self.nx = int(config['nx'])
        self.ny = int(config['ny'])

        self.eps = str(config['eps'])
        self.alpha = str(config['alpha'])
        self.beta = str(config['beta'])

        self.mu_min = str(config['mu_min'])
        self.mu_max = str(config['mu_max'])

        self.fftw_wisdoms = []
        for wisdom_file in config['fftw_wisdoms']:
            with open(wisdom_file, 'rb') as f:
                self.fftw_wisdoms.append(pickle.load(f))

        self.runs = []

        for run_config in config['runs']:
            self.runs.append(UnitCellSingleRunConfig(self, run_config))

        self.savedir = f'{self.nx}x{self.ny}/eps_{self.eps}/alpha_{self.alpha}/beta_{self.beta}'

def parse_config(fname: str = 'config.yaml'):
    with open(fname, 'r') as f:
        config = yaml.safe_load(f)

    return UnitCellSimulationConfig(config)
