
# Introduction

`pfc_interface` is a collection of python scripts based on `pfc-util` that
generates, evolves, and stores PFC solid, liquid, and interface profiles.
The principal objective is to measure the interfacial energy $\gamma$, interface width $w$, and 
the anisotropy parameter $\alpha_\gamma$.

Currently it contains three main modules:

- `unit_cell`: Generate liquid and solid unit cells in equilibrium
- `gen_interface`: Generate interfaces
- `run_interface`: Generate a


```
python main.py MODULE -c CONFIG [--dry]
```


# `unit_cell`

Generate and evolve unit cells under constant chemical potential $\mu$.
The $\mu$ such that liquid and relaxed solid have the same grand potential will
also be searched for.

The program follows the cycle of

1. Choose a $\mu$ based on the current range, previous values, and $\omega_l$,$\omega_s$ 
2. Relax solid unit cell under $\mu$
3. Resize liquid unit cell to match solid's, and minimize under $\mu$
4. Compute $\omega_l$ and $\omega_s$
5. Repeat until the range of $\mu$ is narrower than the desired precision.

## Generated Assets

- `data/[nx]x[ny]/eps_[eps]/alpha_[alpha]/beta_[beta]/
    - `log.pkl`: log file, contains a list of `MuSearchRecord` objects corresponding to each run
    - `unit_sol.field`: final unit cell solid field
    - `unit_liq.field`: final unit cell liquid field


## Parameters
- source: the source fields, can either be from `pfc.toolkit` or file path

- nx, ny: unit cell shape
  
- eps, alpha, beta: PFC parameters

- mu_min, mu_max: initial range of $\mu$

- fftw_wisdoms: FFTW wisdom paths

- runs: Each session can have multiple runs, see below


### Per-Run Parameters
- precision: floating point precision

- dt: simulation time step

- mu_precision: 

- search_method: search algorithm for $\mu$

- fft_threads: number of threads used for FFT

- n_steps: (refer to `torusgrid.dynamics`)
- refresh_interval: (refer to `torusgrid.dynamics`)

- target: stopping target
- tol: stopping tolerance
- patience: stopping patience

- wisdom_only: whether to allow transforms with wisdom already imported

- expand_range: the magnitude by which to expand the final $\mu$ range
    

# `gen_interface`
Make sure data/eps_[epsilon]/alpha_[alpha]/beta_[beta] is populated with
`unit_sol.field`, `unit_liq.field`, and `log.pkl`

Generate a rotated long field for interface calculations (PFC6).

This module follows the following procedure to generate a solid-liquid
interface.

1. Generate rotated unit cells

2. Minimize rotated solid and liquid unit cells
    - runs constant chemcial potential minimization on the generated solid and liquid unit cells
    - mu is manually specified in glnobal_config.py

3. Elongate solid and liquid

4. Minimize long solid and liquid fields
    - runs nonlocal conserved RK4 minimization on long solid and liquid fields

5. Make interface

6. Save fields

## Generated Assets

- `data/[nx]x[ny]/eps_[eps]/alpha_[alpha]/beta_[beta]/theta_[theta]/`
    - `liquid.field`: liquid field after rotation
    - `solid.field`: solid field after rotation
    - `long_liquid.field`: extended solid field
    - `long_solid.field`: extend liquid field
    - `interface.field`: interface field

## Parameters

- precision: floating point precision

- na, nb: orientation vector

- eps, alpha, beta: PFC parameters

- dt: time step

- fftw_wisdoms: FFTW wisdom paths

- n_step

- mx, my: solid/liquid field extension factors


- width: Generated interface width

# `run_interface`

## Generated Assets

- `data/[nx]x[ny]/eps_[eps]/alpha_[alpha]/beta_[beta]/theta_[theta]/interfaces/`
    - `0000.field`, `0001.field`, ... : long interface fields

## Parameters


