import numpy as np
import torusgrid as tg
import pfc_util as pfc


dry = False

fname = group_name

if dry: print('dry run')


ifc = tg.load(tg.RealField2D, f'{file_prefix}/interface.field')
solid = tg.load(tg.RealField2D, f'{file_prefix}/solid.field')
liquid = tg.load(tg.RealField2D, f'{file_prefix}/liquid.field')

delta_sol = tg.extend(solid, Mx_delta, My)
delta_liq = tg.extend(liquid, Mx_delta, My)

######################################################################################################

try:
    group = pfc.load_pfc_group(f'{file_prefix}/{fname}.pfcgroup')
    model_previous = group.get_sorted_models('Lx')[-1]
    ifc = model_previous.field
    N = len(group.get_names())
    i = N
    print(f'continuing in {file_prefix}/, found {N} interface fields')

except FileNotFoundError as e:
    group = pfc.PFCGroup()
    print(f'{file_prefix}/: empty')
    i = 0

print(file_prefix)

def end_program(x: dn.FancyEvolver):
    x.set_continue_flag(False)
    raise KeyboardInterrupt

while True:
    print(f'{i+1}')
    model, ifc2 = routine.evolve_and_elongate_interface(ifc, delta_sol, delta_liq, 
            minimizer_supplier=minim_supplier,
            N_steps=N_steps, N_epochs=None, 
            interrupt_handler=end_program,
            display_format=dfmt, callbacks=[es_F], verbose=False)

    dim1 = ifc.get_dimensions()
    dim2 = ifc2.get_dimensions()
    print(f'evolved L({dim1[0]:.4f}, {dim1[1]:.4f}) N({dim1[2]}, {dim1[3]})')
    print(f'elongated to L({dim2[0]:.4f}, {dim2[1]:.4f}) N({dim2[2]}, {dim2[3]})')
    group.put(model, f'long_{i:03d}')
    if not dry:
        group.save(f'{file_prefix}/{fname}')
        print(f'saved group to {file_prefix}/{fname}')
    ifc = ifc2
    i += 1

