import numpy as np
import torusgrid as tg
import pfc_util as pfc
import rich
import pyfftw
from pathlib import Path

from .config import parse_config

from .data import get_interface_list


def run(config_name: str, *, dry: bool = False):
    console = rich.get_console()
    if dry:
        console.log('[bold bright_cyan]Dry run[/bold bright_cyan]')

    C = parse_config(config_name)

    for wisdom in C.fftw_wisdoms:
        pyfftw.import_wisdom(wisdom)

    if dry: print('dry run')

    console.log(f'Saving directory: data/{C.file_prefix(True)}')

    ifc = tg.load(tg.RealField2D, f'./data/{C.file_prefix(True)}/interface.field')
    solid = tg.load(tg.RealField2D, f'./data/{C.file_prefix(True)}/solid.field')
    liquid = tg.load(tg.RealField2D, f'./data/{C.file_prefix(True)}/liquid.field')

    delta_sol = tg.extend(solid, (C.mx_delta, C.my))
    delta_liq = tg.extend(liquid, (C.mx_delta, C.my))

    ######################################################################################################
    ifc_loaders = get_interface_list(f'./data/{C.file_prefix(True)}/interfaces')

    n_ifcs = len(ifc_loaders)
    i = n_ifcs
    
    if n_ifcs > 0:
        console.log(f'continuing in data/{C.file_prefix(True)}/interfaces/, found {n_ifcs} interface fields')
        ifc = ifc_loaders[-1]()
    else:
        console.log(f'No previous interfaces found, starting fresh')
        Path(f'data/{C.file_prefix(True)}/interfaces').mkdir(exist_ok=True)

    def minim_supplier(field: tg.RealField2D):
        m = pfc.pfc6.NonlocalConservedRK4(field, C.dt, C.eps_, C.alpha_, C.beta_)
        m.initialize_fft(
                threads=C.fft_threads,
                wisdom_only=C.wisdom_only,
                destroy_input=True)
        return m

    hooks = pfc.toolkit.get_pfc_hooks(
        state_function_cls=pfc.pfc6.StateFunction,
        display_digits=-round(np.log10(C.tol)),
        extra_display_digits=2,
        title_params=['eps', 'alpha', 'beta', 'R', 'M', 'dt'],
        display_params=['Lx', 'Ly', 'psibar', 'f', 'F'],
        refresh_interval=C.refresh_interval,
        detect_slow=(C.target, C.tol, C.patience),
        fps=C.fps
    )

    while True:
        console.rule()
        console.log(f'Evolving interface {i}')
        console.log(f'size={ifc.size} shape={ifc.shape}')

        ifc2 = pfc.toolkit.evolve_and_elongate_interface(
            ifc, delta_sol, delta_liq,     
            minimizer_supplier=minim_supplier,
            n_steps=C.n_steps, hooks=hooks,
            verbose=True
        )

        console.log(f'evolved size={ifc.size} shape={ifc.shape}')
        console.log(f'elongated to size={ifc2.size} shape={ifc2.shape}')

        if not dry:
            field_path = f'data/{C.file_prefix(True)}/interfaces/{i:04d}.field'
            tg.save(ifc, field_path)
            console.log(f'saved interface to {field_path}')

        ifc = ifc2
        i += 1


