import os
from typing import List
import torusgrid  as tg
import pfc_util as pfc
import pickle
from pathlib import Path
import rich
import pyfftw

from .config import UnitCellSimulationConfig, parse_config
from .singlerun import run_single

from ..base import CommandLineConfig
from .. import base

from .. import global_cfg as G



def run(config_name: str, CC: CommandLineConfig):
    C = parse_config(config_name)
    console = rich.get_console()
    savedir = C.file_path('pfc')
    
    
    _running_marker = Path(savedir + '/' + G.RUNNING_FILE)
    
    if _running_marker.exists():
        console.log(f'{str(_running_marker.parent)} is already occupied by another process. Aborted.', style='bold red', highlight=False)
        return

    if not CC.dry:
        Path(savedir).mkdir(parents=True, exist_ok=True)
        base.check_dir_empty(savedir, overwrite=CC.overwrite)

    try:
        if not CC.dry:
            _running_marker.touch()
        _run(C, CC)

    finally:
        if not CC.dry:
            os.remove(_running_marker)
    

def _run(C: UnitCellSimulationConfig, CC: CommandLineConfig):

    console = rich.get_console()

    '''Load FFTW wisdoms'''
    for wisdom in C.fftw_wisdoms:
        pyfftw.import_wisdom(wisdom)


    '''Resize the solid to the desired shape'''
    if (C.nx,C.ny) != (C.source_field.shape):
        sol = tg.resample(C.source_field, shape=(C.nx,C.ny), order=1)
        console.log(f'Resized solid shape to configured shape: {(C.nx,C.ny)} -> {C.source_field.shape}')
    else:
        sol = C.source_field
        console.log(f'Source field already has the configured shape {C.source_field.shape}')


    '''Make liquid'''
    liq = tg.const_like(sol)

    '''Saving destination'''
    savedir = C.file_path("pfc")
    console.log(f'saving directory: {savedir}')


    '''Do mu search'''
    console.log(f'found {len(C.runs)} runs')

    recs: List[pfc.toolkit.MuSearchRecord] = []

    mu_max = C.mu_max
    mu_min = C.mu_min
    for i, cfg in enumerate(C.runs):
        console.rule(style='orange3')
        console.log(f'Run {i+1}/{len(C.runs)}')

        mu_max = cfg.dtype(mu_max)
        mu_min = cfg.dtype(mu_min)

        sol, liq, rec = run_single(cfg, mu_min, mu_max, sol)

        if pfc.is_liquid(sol.psi, tol=cfg.liquid_tol):
            console.log(f'[bold red]Solid field has been liquefied.[/bold red]')
            console.log(f'[bold red]Results will not be saved.[/bold red]')
            console.log(f'[bold red]Aborted.[/bold red]')
            return

        mu_min = rec.lower_bound - cfg.expand_range
        mu_max = rec.upper_bound + cfg.expand_range


        recs.append(rec)


    '''Save fields'''
    if not CC.dry:
        console.log(f'saving under {savedir}')
        tg.save(sol, f'{savedir}/unit_sol.field')
        tg.save(liq, f'{savedir}/unit_liq.field')
        with open(f'{savedir}/log.pkl', 'wb') as f:
            pickle.dump(recs, f)

