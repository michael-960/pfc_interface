

# unit_cell



# gen_interface

This is the entry point of the interface module of NPFC/PFC6.
Make sure data/eps_[epsilon]/alpha_[alpha]/ is populated with unit_sol.field and unit_liq.field

Generate a rotated long field for interface calculations (PFC6).

## Parameters:

    - na, nb: orientation vector
    - eps_str: PFC6 epsilon
    - alpha: PFC6 alpha
    - mu: chemical potential

    - dt: time step
    - inertia: RK4 inertia
    - N_step: command line output time step interval

    - Mx0, My: solid/liquid field elongation factors

    - width0: Generated interface width



1. Generate rotated unit cells

2. Minimize rotated solid and liquid unit cells
    - runs constant chemcial potential minimization on the generated solid and liquid unit cells
    - mu is manually specified in global_config.py

3. Elongate solid and liquid

4. Minimize long solid and liquid fields
    - runs nonlocal conserved RK4 minimization on long solid and liquid fields

5. Make interface

6. Save fields
    - saved assets:
        - [file_prefix]/interface.field     interface field file
        - [file_prefix]/solid.field         solid field file
        - [file_prefix]/liquid.field        liquid field file


