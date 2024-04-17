# Copyright 2024 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Config for ITER hybrid scenario based parameters with nonlinear solver.

ITER hybrid scenario based (roughly) on van Mulders Nucl. Fusion 2021.
With Newton-Raphson stepper and adaptive timestep (backtracking)
"""

from torax import config as config_lib
from torax import geometry
from torax import sim as sim_lib
from torax.sources import source_config
from torax.stepper import nonlinear_theta_method
from torax.time_step_calculator import fixed_time_step_calculator


def get_config() -> config_lib.Config:
  # NOTE: This approach to building the config is changing. Over time more
  # parts of this config will be built with pure Python constructors in
  # `get_sim()`.
  return config_lib.Config(
      plasma_composition=config_lib.PlasmaComposition(
          # physical inputs
          Ai=2.5,  # amu of main ion (if multiple isotope, make average)
          Zeff=1.6,  # needed for qlknn and fusion power
          # effective impurity charge state assumed for matching dilution=0.862.
          Zimp=10,
      ),
      profile_conditions=config_lib.ProfileConditions(
          Ip={0: 3, 80: 10.5},  # total plasma current in MA
          # boundary + initial conditions for T and n
          Ti_bound_left=6,  # initial condition ion temperature for r=0
          Ti_bound_right=0.1,  # boundary condition ion temperature for r=Rmin
          Te_bound_left=6,  # initial condition electron temperature for r=0
          Te_bound_right=0.1,  # boundary condition electron temp for r=Rmin
          ne_bound_right_is_fGW=True,
          # boundary condition density for r=Rmin
          ne_bound_right={0: 0.1, 80: 0.3},
          # set initial condition density according to Greenwald fraction.
          nbar_is_fGW=True,
          nbar=1,
          npeak=1.5,  # Initial peaking factor of density profile
          # internal boundary condition (pedestal)
          # do not set internal boundary condition if this is False
          set_pedestal=True,
          Tiped=1.0,  # ion pedestal top temperature in keV for Ti and Te
          Teped=1.0,  # electron pedestal top temperature in keV for Ti and Te
          neped_is_fGW=True,
          # pedestal top electron density in units of nref
          neped={0: 0.3, 80: 0.7},
          Ped_top=0.9,  # set ped top location in normalized radius
      ),
      numerics=config_lib.Numerics(
          # simulation control
          t_final=80,  # length of simulation time in seconds
          fixed_dt=2,
          # 1/multiplication factor for sigma (conductivity) to reduce current
          # diffusion timescale to be closer to heat diffusion timescale.
          resistivity_mult=1,
          # multiplier for ion-electron heat exchange term for sensitivity
          Qei_mult=1,
          # Multiplication factor for bootstrap current
          bootstrap_mult=1,
          # numerical (e.g. no. of grid points, other info needed by solver)
          nr=25,  # radial grid points
          ion_heat_eq=True,
          el_heat_eq=True,
          current_eq=True,
          dens_eq=True,
          maxdt=0.5,
          # multiplier in front of the base timestep dt=dx^2/(2*chi). Can likely
          # be increased further beyond this default.
          dtmult=30,
          dt_reduction_factor=3,
          # effective source to dominate PDE in internal boundary condtion
          # location if T != Tped
          largeValue_T=1.0e10,
          # effective source to dominate density PDE in internal boundary
          # condtion location if n != neped
          largeValue_n=1.0e8,
      ),
      # external heat source parameters
      w=0.07280908366127758,  # Gaussian width in normalized radial coordinate
      rsource=0.12741589640723575,  # Source Gauss peak in normalized r
      Ptot=20.0e6,  # total heating
      el_heat_fraction=1.0,  # electron heating fraction
      # particle source parameters
      # pellets behave like a gas puff for this simulation with exponential
      # decay therefore use the "puff" structure for pellets
      # exponential decay length of gas puff ionization (normalized radial
      # coordinate)
      puff_decay_length=0.3,
      S_puff_tot=0.0e21,  # total pellet particles/s
      # Gaussian width of pellet deposition (normalized radial coordinate) in
      # continuous pellet model
      pellet_width=0.1,
      # Pellet source Gaussian central location (normalized radial coordinate)
      # in continuous pellet model
      pellet_deposition_location=0.85,
      # total pellet particles/s (continuous pellet model)
      S_pellet_tot=0.0e22,
      # NBI particle source Gaussian width (normalized radial coordinate)
      nbi_particle_width=0.25,
      # NBI particle source Gaussian central location (normalized radial
      # coordinate)
      nbi_deposition_location=0.3,
      S_nbi_tot=0.0e20,  # NBI total particle source
      # external current profiles
      fext=0.15,  # total "external" current fraction
      # width of "external" Gaussian current profile (normalized radial
      # coordinate)
      wext=0.075,
      # radius of "external" Gaussian current profile (normalized radial
      # coordinate)
      rext=0.36,
      transport=config_lib.TransportConfig(
          transport_model='qlknn',
          DVeff=True,
          coll_mult=0.25,
          # set inner core transport coefficients (ad-hoc MHD/EM transport)
          apply_inner_patch=True,
          De_inner=0.25,
          Ve_inner=0.0,
          chii_inner=1.5,
          chie_inner=1.5,
          rho_inner=0.3,  # radius below which patch transport is applied
          # set outer core transport coefficients (L-mode near edge region)
          apply_outer_patch=True,
          De_outer=0.1,
          Ve_outer=0.0,
          chii_outer=2.0,
          chie_outer=2.0,
          rho_outer=0.9,  # radius above which patch transport is applied
          # For QLKNN model
          include_ITG=True,  # to toggle ITG modes on or off
          include_TEM=True,  # to toggle TEM modes on or off
          include_ETG=True,  # to toggle ETG modes on or off
          # ensure that smag - alpha > -0.2 always, to compensate for no slab
          # modes
          avoid_big_negative_s=True,
          # minimum |R/Lne| below which effective V is used instead of
          # effective D
          An_min=0.05,
          ITG_flux_ratio_correction=1,
          # allowed chi and diffusivity bounds
          chimin=0.05,  # minimum chi
          chimax=100,  # maximum chi (can be helpful for stability)
          Demin=0.05,  # minimum electron diffusivity
          Demax=50,  # maximum electron diffusivity
          Vemin=-10,  # minimum electron convection
          Vemax=10,  # minimum electron convection
          smoothing_sigma=0.1,
      ),
      solver=config_lib.SolverConfig(
          predictor_corrector=True,
          corrector_steps=10,
          # (deliberately) large heat conductivity for Pereverzev rule
          chi_per=30,
          # (deliberately) large particle diffusion for Pereverzev rule
          d_per=15,
          # use_pereverzev is only used for the linear solver
          use_pereverzev=True,
          log_iterations=True,
      ),
      sources=dict(
          fusion_heat_source=source_config.SourceConfig(
              # incorporate fusion heating source in calculation.
              source_type=source_config.SourceType.MODEL_BASED,
          ),
          ohmic_heat_source=source_config.SourceConfig(
              source_type=source_config.SourceType.ZERO,
          ),
      ),
  )


def get_geometry(config: config_lib.Config) -> geometry.Geometry:
  return geometry.build_chease_geometry(
      config,
      geometry_file='ITER_hybrid_citrin_equil_cheasedata.mat2cols',
      Ip_from_parameters=True,
      Rmaj=6.2,  # major radius (R) in meters
      Rmin=2.0,  # minor radius (a) in meters
      B0=5.3,  # Toroidal magnetic field on axis [T]
  )


def get_sim() -> sim_lib.Sim:
  config = get_config()
  geo = get_geometry(config)
  return sim_lib.build_sim_from_config(
      config=config,
      geo=geo,
      stepper_builder=nonlinear_theta_method.NewtonRaphsonThetaMethod,
      time_step_calculator=fixed_time_step_calculator.FixedTimeStepCalculator(),
  )
