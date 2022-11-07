import numpy as np
import torusgrid as tg
import pfc_util as pfc
import rich
import pyfftw
from pathlib import Path
import shutil

from .config import parse_config

from .. import global_cfg as G

from .. import base
from ..base import CommandLineConfig


def run(config_path: str, CC: CommandLineConfig):

    console = rich.get_console()

    C = parse_config(config_path)

    for wisdom in C.fftw_wisdoms:
        pyfftw.import_wisdom(wisdom)

    console.log(f'Saving directory: {C.file_path("angle")}')

    ifc = tg.load(tg.RealField2D, f'{C.file_path("angle")}/interface.field')
    solid = tg.load(tg.RealField2D, f'{C.file_path("angle")}/solid.field')
    liquid = tg.load(tg.RealField2D, f'{C.file_path("angle")}/liquid.field')

    delta_sol = tg.extend(solid, (C.mx_delta, C.my))
    delta_liq = tg.extend(liquid, (C.mx_delta, C.my))

    ######################################################################################################
    savedir = f'{C.file_path("angle")}/{G.INTERFACES_DIR}'
    if CC.overwrite:
        console.input(f'[bold red]Passing --overwrite will erase all data under {savedir}, proceed?[/bold red]')
        shutil.rmtree(savedir)
        Path(savedir).mkdir()

    ifc_loaders = base.get_interface_list(savedir)


    n_ifcs = len(ifc_loaders)
    i = n_ifcs
    
    if n_ifcs > 0:
        console.log(f'continuing in {C.file_path("angle")}/interfaces/, found {n_ifcs} interface fields')
        ifc = ifc_loaders[-1]()
        ifc = pfc.toolkit.elongate_interface(ifc, delta_sol, delta_liq)
    else:
        console.log(f'No previous interfaces found, starting fresh')
        Path(f'{C.file_path("angle")}/interfaces').mkdir(exist_ok=True)

    def minim_supplier(field: tg.RealField2D):
        m = pfc.pfc6.NonlocalConservedRK4(
                field, 
                C.dt, C.eps_, C.alpha_, C.beta_,
                inertia=C.inertia_, k_regularizer=C.k_regularizer_)

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

        if not CC.dry:
            field_path = f'{C.file_path("angle")}/{G.INTERFACES_DIR}/{i:04d}.field'
            tg.save(ifc, field_path)
            console.log(f'saved interface to {field_path}')

        ifc = ifc2
        i += 1

