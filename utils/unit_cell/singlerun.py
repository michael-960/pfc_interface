import torusgrid  as tg
import pfc_util as pfc
import numpy as np
import rich

from .config import UnitCellSingleRunConfig

console = rich.get_console()


def run_single(
    cfg: UnitCellSingleRunConfig,
    mu_min: tg.FloatLike, mu_max: tg.FloatLike, 
    sol: tg.RealField2D
):

    sol = tg.change_precision(
            sol, 
            tg.FloatingPointPrecision.from_dtype(cfg.dtype))

    console.log(f'shape={sol.shape}')
    console.log(f'size={sol.size}')
    console.log(f'precision={sol.precision}')
    
    console.log(f'search method={cfg.search_method}')
    console.log(f'mu min={np.format_float_scientific(mu_min, precision=-round(np.log10(cfg.mu_precision)))}')
    console.log(f'mu max={np.format_float_scientific(mu_max, precision=-round(np.log10(cfg.mu_precision)))}')

        
    fef = pfc.pfc6.FreeEnergyFunctional(
            cfg.eps_, cfg.alpha_, cfg.beta_)

    def relaxer_supplier(field: tg.RealField2D, /, mu: tg.FloatLike):
        m = pfc.pfc6.StressRelaxer(field, cfg.dt, cfg.eps_, cfg.alpha_, cfg.beta_, mu)
        m.initialize_fft(
                    threads=cfg.fft_threads,
                    wisdom_only=cfg.wisdom_only, 
                    destroy_input=True)
        return m

    def const_mu_supplier(field: tg.RealField2D, /, mu: tg.FloatLike):
        m = pfc.pfc6.ConstantMuMinimizer(field, cfg.dt, cfg.eps_, cfg.alpha_, cfg.beta_, mu)
        m.initialize_fft(
                    threads=cfg.fft_threads,
                    wisdom_only=cfg.wisdom_only,
                    destroy_input=True)
        return m

    hooks = pfc.toolkit.get_pfc_hooks(
        state_function_cls=pfc.pfc6.StateFunction,
        display_digits=round(-np.log10(cfg.mu_precision)),
        extra_display_digits=3,
        title_params=['eps', 'alpha', 'beta', 'mu', 'dt'], 
        refresh_interval=cfg.refresh_interval,
        detect_slow=(cfg.target, cfg.tol, cfg.patience),
        fps=12
    )


    hooks = hooks + (
            tg.dynamics.MonitorValues[tg.dynamics.FieldEvolver[tg.RealField2D]](
                {'psi_delta': lambda e: e.field.psi.max() - e.field.psi.min()}
            ) +
            tg.dynamics.Text('psi_delta: {psi_delta:.4e}')
            )

    rec = pfc.toolkit.find_coexistent_mu(
        sol, mu_min, mu_max, fef,
        relaxer_supplier=relaxer_supplier,
        relaxer_hooks=hooks, relaxer_nsteps=cfg.n_steps,
        const_mu_supplier=const_mu_supplier,
        const_mu_hooks=hooks, const_mu_nsteps=cfg.n_steps,
        precision=cfg.mu_precision,
        search_method=cfg.search_method,
        liquid_tol=cfg.liquid_tol
    )

    liq = tg.const_like(sol)
    mu = rec.mu[-1]

    console.log(f'Evolving liquid profile at mu = {mu}')
    const_mu_supplier(liq, mu).run(cfg.n_steps, hooks=hooks)

    return sol, liq, rec

