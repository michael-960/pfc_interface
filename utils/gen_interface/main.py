import numpy as np
from pathlib import Path
import torusgrid as tg
import pfc_util as pfc
import rich
import pyfftw

from .config import InterfaceGenConfig, parse_config
import os

from .. import base
from ..base import CommandLineConfig
from .. import global_cfg as G


def run(config_path: str, CC: CommandLineConfig):
    C = parse_config(config_path)
    console = rich.get_console()

    savedir = C.file_path('angle')
    
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


def _run(C: InterfaceGenConfig, CC: CommandLineConfig):
    console = rich.get_console()


    for wisdom in C.fftw_wisdoms:
        pyfftw.import_wisdom(wisdom)

    fef = pfc.pfc6.FreeEnergyFunctional(C.eps_, C.alpha_, C.beta_)

    '''Log parameters'''
    console.rule(title='0. Config Parameters')

    savedir = C.file_path("pfc")
    savedir_with_angle = C.file_path("angle")

    console.log(f'reading from {savedir}')
    console.log(f'saving to {savedir_with_angle}')

    console.log(f'precision = {C.precision}')
    console.log(f'eps = {C.eps_}')
    console.log(f'alpha = {C.alpha_}')
    console.log(f'beta = {C.beta_}')
    console.log(f'mu = {C.mu_}')

    console.log(f'(na, nb) = {(C.na, C.nb)}')
    console.log(f'theta = {C.theta}')

    console.log(f'width0 = {C.long.width}')

    console.input('Press enter to proceed')


    '''1. Generate rotated unit cell'''
    console.rule(title='1. Generate rotated unit cell')

    sol0 = tg.change_precision(
        tg.load(tg.RealField2D, f'{savedir}/unit_sol.field'),
        C.precision)

    liq0 = tg.change_precision(
        tg.load(tg.RealField2D, f'{savedir}/unit_liq.field'),
        C.precision)

    console.log(f'Loaded solid field, shape={sol0.shape}, size={sol0.size}')
    console.log(f'Loaded liquid field, shape={liq0.shape}, size={liq0.size}')

    Lx0 = tg.pi(C.precision) * 4
    f = sol0.lx / Lx0

    solid = C.rotator(sol0, pfc.toolkit.SNAP)
    liquid = C.rotator(liq0, pfc.toolkit.SNAP)

    console.log(f'Rotated solid field, shape={solid.shape}, size={solid.size}')
    console.log(f'Rotated liquid field, shape={liquid.shape}, size={liquid.size}')


    '''2. Minimize unit cells'''
    console.rule(title='2. Minimize rotated solid and liquid unit cells')
    hooks_base = pfc.toolkit.get_pfc_hooks(
        state_function_cls=pfc.pfc6.StateFunction,
        display_digits=round(-np.log10(C.base.tol)), 
        extra_display_digits=3,
        detect_slow=(C.base.target, C.base.tol, C.base.patience),
        refresh_interval=C.base.refresh_interval,
        fps = C.base.fps,
        title_params=['eps', 'alpha', 'beta', 'mu', 'dt']
    )


    console.log('Minimizing solid ...')
    m = pfc.pfc6.ConstantMuMinimizer(solid, C.base.dt, C.eps_, C.alpha_, C.beta_, C.mu_)
    m.initialize_fft(threads=C.base.fft_threads,
                     wisdom_only=C.base.wisdom_only,
                     destroy_input=True)
    m.run(C.base.n_steps, hooks_base)

    console.log('Minimizing liquid ...')
    m = pfc.pfc6.ConstantMuMinimizer(liquid, C.base.dt, C.eps_, C.alpha_, C.beta_, C.mu_)
    m.initialize_fft(threads=C.base.fft_threads,
                     wisdom_only=C.base.wisdom_only,
                     destroy_input=True)
    m.run(C.base.n_steps, hooks_base)

    console.log('Minimization done')
    console.log(f'omega_s = {fef.mean_grand_potential_density(solid, C.mu_)}')
    console.log(f'omega_l = {fef.mean_grand_potential_density(liquid, C.mu_)}')


    '''3. Elongate solid and liquid'''
    console.rule(title='3. Elongate solid and liquid')
    long_sol = tg.extend(solid, (C.long.mx, C.long.my))
    long_liq = tg.extend(liquid, (C.long.mx, C.long.my))

    console.log(f'Lx/Lx0 = {long_sol.lx / (4*tg.pi(C.precision))}')
    console.log(f'Ly/Ly0 = {long_sol.ly / (4*tg.pi(C.precision))/np.sqrt(C.dtype(3))}')

    console.log(f'New solid shape = {long_sol.shape}')
    console.log(f'New solid size = {long_sol.size}')

    console.log(f'New liquid shape = {long_liq.shape}')
    console.log(f'New liquid size = {long_liq.size}')


    '''4. Minimize elongated fields'''
    console.rule(title='4. Minimize long solid and liquid fields')

    hooks_long = pfc.toolkit.get_pfc_hooks(
        state_function_cls=pfc.pfc6.StateFunction,
        display_digits=round(-np.log10(C.long.tol)), 
        extra_display_digits=3,
        detect_slow=(C.long.target, C.long.tol, C.long.patience),
        refresh_interval=C.long.refresh_interval,
        fps = C.long.fps,
        display_params=['Lx', 'Ly', 'psibar', 'f', 'F'],
        title_params=['eps', 'alpha', 'beta', 'dt', 'M', 'R']
    )

    console.log('Minimizing long solid ...')
    m = pfc.pfc6.NonlocalConservedRK4(
            long_sol, C.long.dt,
            C.eps_, C.alpha_, C.beta_,
            inertia=C.long.inertia_, k_regularizer=C.long.k_regularizer_)
    m.initialize_fft(threads=C.long.fft_threads,
                     wisdom_only=C.long.wisdom_only,
                     destroy_input=True)
    m.run(C.long.n_steps, hooks_long)

    console.log('Minimizing long liquid ...')
    m = pfc.pfc6.NonlocalConservedRK4(
            long_liq, C.long.dt,
            C.eps_, C.alpha_, C.beta_,
            inertia=C.long.inertia_, k_regularizer=C.long.k_regularizer_)
    m.initialize_fft(threads=C.long.fft_threads,
                     wisdom_only=C.long.wisdom_only,
                     destroy_input=True)
    m.run(C.long.n_steps, hooks_long)

    console.log(f'Long solid mean chemical potential = {fef.derivative(long_sol).mean()}')
    console.log(f'Long liquid mean chemical potential = {fef.derivative(long_liq).mean()}')

    console.log(f'Long solid grand potiential = {fef.grand_potential(long_sol, C.mu_)}')
    console.log(f'Long liquid grand potiential = {fef.grand_potential(long_liq, C.mu_)}')

    console.log(f'Long solid mean grand potiential = {fef.mean_grand_potential_density(long_sol, C.mu_)}')
    console.log(f'Long liquid mean grand potiential = {fef.mean_grand_potential_density(long_liq, C.mu_)}')


    '''5. Make interface'''
    console.rule(title='5. Make and minimize interface field')

    if isinstance(C.long.width, list):
        # test to see which width gives the least energy
        assert len(C.long.width) > 0, 'Supply at least one width'
        console.log(f'Received {len(C.long.width)} widths')
        console.log(f'Testing to see which width gives the least energy')

        F0 = C.long.to_float('inf')
        best = 0

        for i, w in enumerate(C.long.width):
            ifc = tg.blend(long_sol, long_liq, axis=0, interface_width=w)
            F = fef.free_energy(ifc)
            console.log(f'width = {w}, free energy = {F}')
            if F0 is None:
                F0, best = F, i
                best = i
            elif F < F0:
                F0, best = F, i

        console.log(f'Using width {C.long.width[best]}')
        ifc = tg.blend(long_sol, long_liq, axis=0, interface_width=C.long.width[best])

    else:
        console.log(f'Received width = {C.long.width}')
        ifc = tg.blend(long_sol, long_liq, axis=0, interface_width=C.long.width)

    console.log('Minimizing interface ...')
    m = pfc.pfc6.NonlocalConservedRK4(
            ifc, C.long.dt,
            C.eps_, C.alpha_, C.beta_,
            inertia=C.long.inertia_, k_regularizer=C.long.k_regularizer_)

    m.initialize_fft(threads=C.long.fft_threads,
                     wisdom_only=C.long.wisdom_only,
                     destroy_input=True)
    m.run(C.long.n_steps, hooks_long)

    console.log(f'Interface mean density: {ifc.psi.mean()}')
    console.log(f'Interface grand potiential = {fef.grand_potential(ifc, C.mu_)}')
    console.log(f'Interface grand potiential = {fef.mean_grand_potential_density(ifc, C.mu_)}')


    '''5. Save fields'''
    if not CC.dry:
        console.log(f'saving under {savedir_with_angle}')
        Path(savedir_with_angle).mkdir(parents=True, exist_ok=True)

        tg.save(solid, f'{savedir_with_angle}/solid.field')
        tg.save(liquid, f'{savedir_with_angle}/liquid.field')

        tg.save(long_sol, f'{savedir_with_angle}/long_solid.field')
        tg.save(long_liq, f'{savedir_with_angle}/long_liquid.field')

        tg.save(ifc, f'{savedir_with_angle}/interface.field')


