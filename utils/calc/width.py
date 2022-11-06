import numpy as np


from rich.progress import track
from rich import get_console

import torusgrid as tg
import pfc_util as pfc

from .config import parse_config

from .. import base

from ._widthlib import calculate_widths

from .. import global_cfg as G


def run(config_path: str, CC: base.CommandLineConfig):

    console = get_console()
    C = parse_config(config_path)

    calc_file = f'{C.file_path("angle")}/{G.CALC_FILE}'
    if (not CC.dry) and (not CC.overwrite):
        if base.json_has_key(calc_file, 'width'):
            raise base.DataExistsError(f'File {calc_file} already has key \'width\'')


    ifcs_path = f'data/{C.file_prefix("angle")}/interfaces'
    ifcs = base.get_interface_list(ifcs_path)
    

    console.log(f'Loaded {len(ifcs)} fields from {ifcs_path}', highlight=False)

    solid = tg.load(tg.RealField2D, C.solid_file)
    uc_factor_x = solid.lx / (4*tg.pi(C.precision))
    uc_factor_y = solid.ly / (4*tg.pi(C.precision)/np.sqrt(C.to_float('3')))
    uc_factor = (uc_factor_x + uc_factor_y) / 2

    console.log(f'UCFACTOR_X = {uc_factor_x}')
    console.log(f'UCFACTOR_Y = {uc_factor_y}')
    console.log(f'UCFACTOR = {uc_factor}')


    widths = []
    for ifc in track(ifcs, description='Calculating widths'):
        w1, w2, w3 = calculate_widths(ifc(), C.theta, uc_factor=uc_factor)
        widths.append([w1, w2, w3])

    console.print('widths:')
    console.print(widths)

    if not CC.dry:
        base.put_val_into_json(
                calc_file,
                'widths',
                val=np.array(widths).astype(float).tolist())

        console.print(f'interface widths saved to {calc_file}', highlight=False)


