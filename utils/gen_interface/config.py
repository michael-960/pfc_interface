from __future__ import annotations
from typing import List, final
import yaml
import torusgrid as tg
import pfc_util as pfc
import pickle
from .. import base


@final
class BaseFieldConfig(
    base.SpecifiesSimulationParams,
    base.SpecifiesPrecision,
    base.ConfigBase
    ):
    def __init__(self, config: dict):
        super().__init__(config)


@final
class LongFieldConfig(
    base.SpecifiesSimulationParams,
    base.SpecifiesPrecision,
    base.ConfigBase
):
    def __init__(self, config: dict) -> None:

        super().__init__(config)
        self.mx = int(config['mx'])
        self.my = int(config['my'])

        if isinstance(config['width'], list):
            self.width = [self.to_float(w) for w in config['width']]
        else:
            self.width = self.to_float(config['width'])


@final
class InterfaceGenConfig(
    base.SpecifiesShape,
    base.SpecifiesRotationAngle,
    base.SpecifiesFFTWisdoms,
    base.SpecifiesPFCParams,
    base.SpecifiesPrecision,
    base.ConfigBase
):
    def __init__(self, config: dict):
        super().__init__(config)

        self.eps_ = self.to_float(self.eps)
        self.alpha_ = self.to_float(self.alpha)
        self.beta_ = self.to_float(self.beta)

        self.dt = self.dtype(config['dt'])

        self.base = BaseFieldConfig(
            base.Fallback(config['base'], config, ['precision', 'dt'])
        )

        self.long = LongFieldConfig(
            base.Fallback(config['long'], config, ['precision', 'dt'])
        )

        with open(f'{self.file_path("pfc")}/log.pkl', 'rb') as f:
            self.log: List[pfc.toolkit.MuSearchRecord] = pickle.load(f)

        self.mu_ = self.log[-1].mu[-1]


def parse_config(config_path: str) -> InterfaceGenConfig:

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return InterfaceGenConfig(config)

