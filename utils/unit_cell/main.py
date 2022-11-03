import os
from typing import List
import torusgrid  as tg
import pfc_util as pfc
import numpy as np
import pickle
from pathlib import Path
import rich
import pyfftw


from .config import parse_config
from .singlerun import run_single



def run(config_name: str):
    console = rich.get_console()
    C = parse_config(config_name)

    for wisdom in C.fftw_wisdoms:
        pyfftw.import_wisdom(wisdom)


    if (C.nx,C.ny) != (C.source_field.shape):
        sol = tg.resample(C.source_field, shape=(C.nx,C.ny), order=1)
        console.log(f'Resized solid shape to configured shape: {(C.nx,C.ny)} -> {C.source_field.shape}')
    else:
        sol = C.source_field
        console.log(f'Source field already has the configured shape {C.source_field.shape}')

    liq = tg.const_like(sol)


    savedir = f'./data/{C.savedir}'

    pth = Path(savedir)
    if pth.exists():
        assert pth.is_dir()
        assert os.listdir(str(pth)) == []
    else:
        pth.mkdir(parents=True, exist_ok=False)

    console.log(f'saving directory: {savedir}')


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

        mu_min = rec.lower_bound
        mu_max = rec.upper_bound

        recs.append(rec)


    tg.save(sol, f'{savedir}/unit_sol.field')
    tg.save(liq, f'{savedir}/unit_liq.field')


    with open(f'{savedir}/log.pkl', 'wb') as f:
        pickle.dump(recs, f)




