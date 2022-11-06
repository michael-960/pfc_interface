import json
from rich.progress import track
import torusgrid as tg
import pfc_util as pfc
from matplotlib import pyplot as plt
import numpy as np

from rich import get_console


from .config import parse_config

from ..base import CommandLineConfig
from .. import base
from .. import global_cfg as G


def run(config_path: str, CC: CommandLineConfig):

    C = parse_config(config_path)
    console = get_console()
    fef = pfc.pfc6.FreeEnergyFunctional(C.eps_, C.alpha_, C.beta_)

    
    calc_file = f'{C.file_path("angle")}/{G.CALC_FILE}'
    if (not CC.dry) and (not CC.overwrite):
        if base.json_has_key(calc_file, 'gamma'):
            raise base.DataExistsError(f'File {calc_file} already has key \'gamma\'')


    console.log(f'file prefix: {C.file_prefix("angle")}', highlight=False)
    console.log(f'theta={C.theta:.4f}')
    console.log(f'mu={C.mu_:.15f}')

    console.print()

    ifcs_path = f'data/{C.file_prefix("angle")}/interfaces'
    ifcs = base.get_interface_list(ifcs_path)

    console.print()
    console.log(f'Loaded {len(ifcs)} interfaces from {ifcs_path}', highlight=False)
    console.log(f'Lx max: {ifcs[-1]().lx}')
    console.log(f'Lx min: {ifcs[0]().lx}')
    console.print()

    Lx_ar = []
    Ly_ar = []
    Vol_ar = []
    f_ar = []
    om_ar = []
    Om_ar = []


    for ifc_loader in track(ifcs, description='Calculating interfacial energies'):
        try:
            ifc = ifc_loader()
            if C.lx_max >= ifc.lx >= C.lx_min:
                    Lx_ar.append(ifc.lx) 
                    Ly_ar.append(ifc.ly) 
                    Vol_ar.append(ifc.volume)
                    f_ar.append(fef.mean_free_energy_density(ifc))
                    om_ar.append(fef.mean_grand_potential_density(ifc, C.mu_))
        except Exception as e:
            console.log(f'error occured when loading interface: {e.args}')

    console.rule()
    console.log(f'Using Lx={Lx_ar[0]:.5f}~{Lx_ar[-1]:.5f} ({len(Lx_ar)} interfaces)', highlight=False)

    Lx_ar = np.array(Lx_ar)
    Ly_ar = np.array(Ly_ar)
    Vol_ar = np.array(Vol_ar)
    f_ar = np.array(f_ar)
    om_ar = np.array(om_ar)
    Om_ar = om_ar * Vol_ar

    console.print()
    console.log(f'Reading {C.liquid_file} for reference grand potential', highlight=False)

    unit_liq = tg.load(tg.RealField2D, C.liquid_file)
    omega_l = fef.mean_grand_potential_density(unit_liq, C.mu_)

    console.log(f'omega_l = {omega_l}')

    console.log(f'Reading {C.solid_file} for reference grand potential', highlight=False)
    unit_sol = tg.load(tg.RealField2D, C.solid_file)
    omega_s = fef.mean_grand_potential_density(unit_sol, C.mu_)

    console.log(f'omega_s = {omega_s}')

    Om_excess = Om_ar - omega_l*Vol_ar

    gamma = Om_excess / Ly_ar / 2

    console.rule()

    console.print(f'gamma = ')
    console.print(gamma.tolist())

    console.print(f'free energy density = ')
    console.print(f_ar.tolist())


    if CC.plot:
        fig, axs = plt.subplots(2, 2)

        axs[0,0].scatter(Lx_ar, gamma, color='k')
        axs[0,0].set_xlabel('L')
        axs[0,0].set_ylabel('gamma')

        axs[0,1].scatter(Lx_ar, f_ar, color='k')
        axs[0,1].set_xlabel('L')
        axs[0,1].set_ylabel('f')

        axs[1,0].scatter(Lx_ar, (omega_l-omega_s)*Vol_ar / Ly_ar / 2, color='k')

        plt.show()

    if not CC.dry:


        base.put_val_into_json(
                calc_file, 'gamma',
                val=gamma.astype(float).tolist()
        )

        console.log(f'interfacial energies saved to {calc_file}', highlight=False)


