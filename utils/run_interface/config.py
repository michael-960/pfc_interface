from .. import base
import yaml



class InterfaceRunConfig(
    base.SpecifiesFFTWisdoms,
    base.SpecifiesSimulationParams,
    base.SpecifiesRotationAngle,
    base.SpecifiesPFCParams,
    base.SpecifiesShape,
    base.SpecifiesPrecision,
    base.ConfigBase
):
    def __init__(self, config: dict):
        super().__init__(config)

        self.mx_delta = int(config['mx_delta'])
        self.mx = int(config['mx'])
        self.my = int(config['my'])

        self.eps_ = self.to_float(self.eps)
        self.alpha_ = self.to_float(self.alpha)
        self.beta_ = self.to_float(self.beta)


def parse_config(config_path: str):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return InterfaceRunConfig(config)


