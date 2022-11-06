from .. import base
import yaml
from typing import List, final
import pickle
import pfc_util as pfc


@final
class CalcConfig(
    base.SpecifiesRotationAngle,
    base.SpecifiesPFCParams,
    base.SpecifiesShape,
    base.SpecifiesPrecision,
    base.ConfigBase
    ):

    def __init__(self, config: dict):
        super().__init__(config)

        with open(f'{self.file_path("pfc")}/log.pkl', 'rb') as f:
            self.log: List[pfc.toolkit.MuSearchRecord] = pickle.load(f)

        self.mu_ = self.log[-1].mu[-1]

        self.lx_min = self.to_float(config['lx_min'])
        self.lx_max = self.to_float(config['lx_max'])

        self.eps_ = self.to_float(self.eps)
        self.alpha_ = self.to_float(self.alpha)
        self.beta_ = self.to_float(self.beta)

        self.solid_file = f'{self.file_path("pfc")}/unit_sol.field'
        self.liquid_file = f'{self.file_path("pfc")}/unit_liq.field'
        

def parse_config(path: str):
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return CalcConfig(config)



