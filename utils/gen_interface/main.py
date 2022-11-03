import numpy as np
from pathlib import Path
import torusgrid as tg
import pfc_util as pfc
import rich
import pyfftw

from .config import parse_config


def run(config_name: str):
    console = rich.get_console()

    C = parse_config(config_name)

    for wisdom in C.fftw_wisdoms:
        pyfftw.import_wisdom(wisdom)

    fef = pfc.pfc6.FreeEnergyFunctional(C.eps, C.alpha, C.beta)

    dry = False

    console.rule(title='0. Config Parameters')

    savedir_with_angle = f'./data/{C.file_prefix_with_angle}'
    savedir = f'./data/{C.file_prefix}'

    console.log(f'reading from {savedir}')
    console.log(f'saving to {savedir_with_angle}')

    console.log(f'precision = {C.precision}')
    console.log(f'eps = {C.eps}')
    console.log(f'alpha = {C.alpha}')
    console.log(f'beta = {C.beta}')

    console.log(f'mu = {C.mu}')

    console.log(f'(na, nb) = {(C.na, C.nb)}')
    console.log(f'theta = {C.theta}')

    console.log(f'width0 = {C.long.width0}')

    console.input('Press enter to proceed')

    ###################################################################################
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

    ###################################################################################
    console.rule(title='2. Minimize rotated solid and liquid unit cells')
    hooks_base = pfc.toolkit.get_pfc_hooks(
        state_function_cls=pfc.pfc6.StateFunction,
        display_digits=round(-np.log10(C.base.tol)), 
        extra_display_digits=3,
        detect_slow=(C.base.target, C.base.tol, C.base.patience),
        refresh_interval=C.base.refresh_interval,
        fps = C.fps,
        title_params=['eps', 'alpha', 'beta', 'mu', 'dt']
    )


    console.log('Minimizing solid ...')
    m = pfc.pfc6.ConstantMuMinimizer(solid, C.dt, C.eps, C.alpha, C.beta, C.mu)
    m.initialize_fft(threads=C.base.fft_threads,
                     wisdom_only=C.base.wisdom_only,
                     destroy_input=True)
    m.run(C.base.n_steps, hooks_base)

    console.log('Minimizing liquid ...')
    m = pfc.pfc6.ConstantMuMinimizer(liquid, C.dt, C.eps, C.alpha, C.beta, C.mu)
    m.initialize_fft(threads=C.base.fft_threads,
                     wisdom_only=C.base.wisdom_only,
                     destroy_input=True)
    m.run(C.base.n_steps, hooks_base)

    console.log('Minimization done')
    console.log(f'omega_s = {fef.mean_grand_potential_density(solid, C.mu)}')
    console.log(f'omega_l = {fef.mean_grand_potential_density(liquid, C.mu)}')


    ###################################################################################
    console.rule(title='3. Elongate solid and liquid')
    long_sol = tg.extend(solid, (C.long.mx, C.long.my))
    long_liq = tg.extend(liquid, (C.long.mx, C.long.my))

    console.log(f'Lx/Lx0 = {long_sol.lx / (4*tg.pi(C.precision))}')
    console.log(f'Ly/Ly0 = {long_sol.ly / (4*tg.pi(C.precision))/np.sqrt(C.dtype(3))}')

    console.log(f'New solid shape = {long_sol.shape}')
    console.log(f'New solid size = {long_sol.size}')

    console.log(f'New liquid shape = {long_liq.shape}')
    console.log(f'New liquid size = {long_liq.size}')


    ###################################################################################
    console.rule(title='4. Minimize long solid and liquid fields')
    hooks_long = pfc.toolkit.get_pfc_hooks(
        state_function_cls=pfc.pfc6.StateFunction,
        display_digits=round(-np.log10(C.long.tol)), 
        extra_display_digits=3,
        detect_slow=(C.long.target, C.long.tol, C.long.patience),
        refresh_interval=C.long.refresh_interval,
        fps = C.fps,
        display_params=['Lx', 'Ly', 'psibar', 'f', 'F'],
        title_params=['eps', 'alpha', 'beta', 'dt', 'M', 'R']
    )


    console.log('Minimizing long solid ...')
    m = pfc.pfc6.NonlocalConservedRK4(long_sol, C.dt, C.eps, C.alpha, C.beta)
    m.initialize_fft(threads=C.long.fft_threads,
                     wisdom_only=C.long.wisdom_only,
                     destroy_input=True)
    m.run(C.long.n_steps, hooks_long)

    console.log('Minimizing long liquid ...')
    m = pfc.pfc6.NonlocalConservedRK4(long_liq, C.dt, C.eps, C.alpha, C.beta)
    m.initialize_fft(threads=C.long.fft_threads,
                     wisdom_only=C.long.wisdom_only,
                     destroy_input=True)
    m.run(C.long.n_steps, hooks_long)

    console.log(f'Long solid mean chemical potential = {fef.derivative(long_sol).mean()}')
    console.log(f'Long liquid mean chemical potential = {fef.derivative(long_liq).mean()}')

    console.log(f'Long solid grand potiential = {fef.grand_potential(long_sol, C.mu)}')
    console.log(f'Long liquid grand potiential = {fef.grand_potential(long_liq, C.mu)}')

    console.log(f'Long solid mean grand potiential = {fef.mean_grand_potential_density(long_sol, C.mu)}')
    console.log(f'Long liquid mean grand potiential = {fef.mean_grand_potential_density(long_liq, C.mu)}')


    ###################################################################################
    console.rule(title='5. Make and minimize interface field')
    ifc = tg.blend(long_sol, long_liq, axis=0, interface_width=C.long.width0)

    console.log('Minimizing interface ...')
    m = pfc.pfc6.NonlocalConservedRK4(ifc, C.dt, C.eps, C.alpha, C.beta)
    m.initialize_fft(threads=C.long.fft_threads,
                     wisdom_only=C.long.wisdom_only,
                     destroy_input=True)
    m.run(C.long.n_steps, hooks_long)

    console.log(f'Interface mean density: {ifc.psi.mean()}')

    ###################################################################################

    # 6. Save fields
    if not dry:
        console.log(f'saving under {savedir_with_angle}')
        Path(savedir_with_angle).mkdir(parents=True, exist_ok=True)

        tg.save(solid, f'{savedir_with_angle}/solid.field')
        tg.save(liquid, f'{savedir_with_angle}/liquid.field')

        tg.save(long_sol, f'{savedir_with_angle}/long_solid.field')
        tg.save(long_liq, f'{savedir_with_angle}/long_liquid.field')

        tg.save(ifc, f'{savedir_with_angle}/interface.field')

    console.log(f'Interface grand potiential = {fef.grand_potential(ifc, C.mu)}')
    console.log(f'Interface grand potiential = {fef.mean_grand_potential_density(ifc, C.mu)}')





