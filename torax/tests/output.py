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

"""Unit tests for torax.output."""

from absl.testing import absltest
from absl.testing import parameterized
from jax import numpy as jnp
from jax import tree_util
from torax import core_profile_setters
from torax import geometry
from torax import geometry_provider
from torax import interpolated_param
from torax import output
from torax import state
from torax.config import runtime_params as general_runtime_params
from torax.sources import default_sources
from torax.sources import source as source_lib
from torax.sources import source_profiles as source_profiles_lib
from torax.tests.test_lib import torax_refs


SequenceKey = tree_util.SequenceKey
GetAttrKey = tree_util.GetAttrKey
DictKey = tree_util.DictKey


class StateHistoryTest(parameterized.TestCase):
  """Unit tests for the `torax.output` module."""

  def setUp(self):
    super().setUp()
    runtime_params = general_runtime_params.GeneralRuntimeParams(
        profile_conditions=general_runtime_params.ProfileConditions(
            Ti_bound_right=27.7,
            Te_bound_right={0.0: 42.0, 1.0: 0.0},
            ne_bound_right=interpolated_param.InterpolatedVarSingleAxis(
                {0.0: 0.1, 1.0: 2.0},
                interpolation_mode=interpolated_param.InterpolationMode.STEP,
            ),
        ),
    )
    source_models_builder = default_sources.get_default_sources_builder()
    source_models = source_models_builder()
    # Make some dummy source profiles that could have come from these sources.
    self.geo = geometry.build_circular_geometry()
    ones = jnp.ones(source_lib.ProfileType.CELL.get_profile_shape(self.geo))
    geo_provider = geometry_provider.ConstantGeometryProvider(self.geo)
    dynamic_runtime_params_slice, geo = (
        torax_refs.build_consistent_dynamic_runtime_params_slice_and_geometry(
            runtime_params,
            geo_provider,
            sources=source_models_builder.runtime_params,
        )
    )
    self.source_profiles = source_profiles_lib.SourceProfiles(
        j_bootstrap=source_profiles_lib.BootstrapCurrentProfile.zero_profile(
            geo
        ),
        qei=source_profiles_lib.QeiInfo.zeros(geo),
        profiles={
            'bremsstrahlung_heat_sink': -ones,
            'ohmic_heat_source': ones * 5,
        },
    )

    self.core_profiles = core_profile_setters.initial_core_profiles(
        dynamic_runtime_params_slice=dynamic_runtime_params_slice,
        geo=geo,
        source_models=source_models,
    )
    self.core_transport = state.CoreTransport.zeros(geo)

  def test_state_history_init(self):
    """Smoke test the `StateHistory` constructor."""
    t = jnp.array(0.0)
    dt = jnp.array(0.1)
    sim_state = state.ToraxSimState(
        core_profiles=self.core_profiles,
        core_transport=self.core_transport,
        core_sources=self.source_profiles,
        t=t,
        dt=dt,
        stepper_iterations=1,
        time_step_calculator_state=None,
        stepper_error_state=1,
    )

    output.StateHistory((sim_state,))

  def test_state_history_to_xr(self):
    """Smoke test the `StateHistory.simulation_output_to_xr` method."""
    t = jnp.array(0.0)
    dt = jnp.array(0.1)
    sim_state = state.ToraxSimState(
        core_profiles=self.core_profiles,
        core_transport=self.core_transport,
        core_sources=self.source_profiles,
        t=t,
        dt=dt,
        stepper_iterations=1,
        time_step_calculator_state=None,
        stepper_error_state=1,
    )
    history = output.StateHistory((sim_state,))

    history.simulation_output_to_xr(self.geo)


if __name__ == '__main__':
  absltest.main()
