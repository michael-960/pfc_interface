from __future__ import annotations
from typing import List, Literal, final
import numpy as np
import torusgrid as tg
import pfc_util as pfc
import yaml
from .. import base


@final
class UnitCellSingleRunConfig(
    base.SpecifiesPFCParams,
    base.SpecifiesSimulationParams,
    base.SpecifiesPrecision,
    base.ConfigBase
):
    def __init__(self, config: dict):
        super().__init__(config)

        self.mu_precision = self.dtype(config['mu_precision'])

        self.eps_ = self.dtype(self.eps)
        self.alpha_ = self.dtype(self.alpha)
        self.beta_ = self.dtype(self.beta)

        self.search_method: Literal['binary', 'interpolate']

        self.expand_range = self.to_float(config['expand_range'])

        if str(config['search_method']) == 'binary':
            self.search_method = 'binary'
        else:
            self.search_method = 'interpolate'


@final
class UnitCellSimulationConfig(
    base.SpecifiesShape,
    base.SpecifiesPFCParams,
    base.SpecifiesFFTWisdoms,
    base.ConfigBase
):

    def __init__(self, config: dict) -> None:
        super().__init__(config)

        self.source = config['source']

        if self.source['type'] == 'static':
            self.source_field = pfc.toolkit.get_relaxed_minimized_coexistent_unit_cell(self.source['name'])
        else:
            self.source_field = tg.load(tg.RealField2D, self.source['name'])

        self.mu_min = str(config['mu_min'])
        self.mu_max = str(config['mu_max'])

        self.runs: List[UnitCellSingleRunConfig] = []

        for run_config in config['runs']:
            self.runs.append(
                UnitCellSingleRunConfig(
                    base.Fallback(run_config, config, ['eps', 'alpha', 'beta'])
                )
            )

        self.savedir = base.get_path(self.nx, self.ny, self.eps, self.alpha, self.beta)


def parse_config(fname: str = 'config.yaml'):
    with open(fname, 'r') as f:
        config = yaml.safe_load(f)
    return UnitCellSimulationConfig(config)
