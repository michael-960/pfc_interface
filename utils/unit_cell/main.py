import os
from typing import List
import torusgrid  as tg
import pfc_util as pfc
import pickle
from pathlib import Path
import rich
import pyfftw



from .config import parse_config
from .singlerun import run_single

from ..base import CommandLineConfig



def run(config_name: str, CC: CommandLineConfig):
    console = rich.get_console()
    C = parse_config(config_name)

    if CC.dry:
        console.log('[bold bright_cyan]Dry run[/bold bright_cyan]')


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


    '''Check saving destination's availability'''
    savedir = f'./data/{C.savedir}'
    pth = Path(savedir)
    if pth.exists():
        assert pth.is_dir(), 'Saving location is not directory'
        assert os.listdir(str(pth)) == [], 'Saving directory not empty'
    else:
        ...
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

        mu_min = rec.lower_bound - cfg.expand_range
        mu_max = rec.upper_bound + cfg.expand_range

        recs.append(rec)


    '''Save fields'''
    if not CC.dry:
        console.log(f'saving under {savedir}')
        pth.mkdir(parents=True, exist_ok=True)
        tg.save(sol, f'{savedir}/unit_sol.field')
        tg.save(liq, f'{savedir}/unit_liq.field')

        with open(f'{savedir}/log.pkl', 'wb') as f:
            pickle.dump(recs, f)

