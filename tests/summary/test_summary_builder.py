"""Tests of SummaryBuilder: interpolation on the time base and setting nodes."""

import numpy as np
import pytest


class TestInterpolate:
    def test_linear(self, make_builder):
        builder = make_builder([1.0, 2.0])
        values = builder.interpolate([0.0, 4.0], [0.0, 8.0])
        np.testing.assert_allclose(values, [2.0, 4.0])

    def test_unsorted_source(self, make_builder):
        builder = make_builder([1.0])
        np.testing.assert_allclose(builder.interpolate([2.0, 0.0], [4.0, 0.0]), [2.0])

    def test_nearest(self, make_builder):
        builder = make_builder([0.4, 0.6])
        values = builder.interpolate([0.0, 1.0], [0, 1], nearest=True)
        np.testing.assert_array_equal(values, [0, 1])

    def test_not_covering_time_base(self, make_builder):
        builder = make_builder([1.0, 2.0])
        assert builder.interpolate([1.5, 3.0], [1.0, 2.0]) is None
        assert builder.interpolate([0.0, 1.5], [1.0, 2.0]) is None

    def test_single_source_time(self, make_builder):
        builder = make_builder([2.0])
        np.testing.assert_array_equal(builder.interpolate([2.0], [7.0]), [7.0])
        assert builder.interpolate([3.0], [7.0]) is None

    def test_tolerance_on_time_base(self, make_builder):
        builder = make_builder([2.0946249])
        values = builder.interpolate([2.0946249000063], [5.0])
        np.testing.assert_array_equal(values, [5.0])

    def test_invalid_samples_are_dropped(self, make_builder):
        builder = make_builder([1.0])
        values = builder.interpolate([0.0, 1.0, 2.0], [0.0, np.nan, 4.0])
        np.testing.assert_allclose(values, [2.0])

    @pytest.mark.parametrize(
        "t_src, y_src",
        [(None, [1.0]), ([1.0], None), ([1.0, 2.0], [1.0]), ([1.0], [np.nan])],
    )
    def test_unusable_input(self, make_builder, t_src, y_src):
        assert make_builder([1.0]).interpolate(t_src, y_src) is None


class TestSet:
    def test_value_and_source(self, make_builder):
        builder = make_builder([1.0, 2.0])
        assert builder.set("global_quantities/ip", [1e6, 2e6], "equilibrium/ip")
        ip = builder.ids.global_quantities.ip
        np.testing.assert_array_equal(ip.value, [1e6, 2e6])
        assert ip.source == "equilibrium/ip"
        assert builder.filled == {"global_quantities/ip": "equilibrium/ip"}
        np.testing.assert_array_equal(builder.get("global_quantities/ip"), [1e6, 2e6])

    def test_scalar_broadcast_on_time_base(self, make_builder):
        builder = make_builder([1.0, 2.0])
        builder.set("boundary/strike_point_inner_r", 4.1, "grid")
        np.testing.assert_array_equal(builder.ids.boundary.strike_point_inner_r.value, [4.1, 4.1])

    def test_0d_float(self, make_builder):
        builder = make_builder()
        builder.set("global_quantities/r0", np.array([6.2]), "vtf")
        assert builder.ids.global_quantities.r0.value == 6.2

    def test_int_array(self, make_builder):
        builder = make_builder()
        builder.set("boundary/type", [0.9, 1.1], "eq")
        np.testing.assert_array_equal(builder.ids.boundary.type.value, [1, 1])
        assert builder.ids.boundary.type.value.dtype.kind == "i"

    def test_string(self, make_builder):
        builder = make_builder()
        assert builder.set("configuration", "LIMITER", "grid")
        assert builder.ids.configuration.value == "LIMITER"
        assert not builder.set("code/name", "", "x")

    def test_leaf_without_source(self, make_builder):
        builder = make_builder()
        builder.set("local/magnetic_axis/position/r", [6.0, 6.1], "eq")
        np.testing.assert_array_equal(builder.ids.local.magnetic_axis.position.r, [6.0, 6.1])

    def test_first_wins_and_replace(self, make_builder):
        builder = make_builder([1.0])
        assert builder.set("global_quantities/ip", [1.0], "first")
        assert not builder.set("global_quantities/ip", [2.0], "second")
        assert builder.ids.global_quantities.ip.source == "first"
        assert builder.set("global_quantities/ip", [3.0], "third", replace=True)
        assert builder.ids.global_quantities.ip.source == "third"

    def test_aos_is_resized(self, make_builder):
        builder = make_builder([1.0])
        builder.set("heating_current_drive/ec[2]/power_launched", [1e6], "ec")
        assert len(builder.ids.heating_current_drive.ec) == 3

    @pytest.mark.parametrize(
        "path, value",
        [
            ("global_quantities/ip", [1.0]),  # wrong length
            ("global_quantities/ip", [1.0, np.nan]),  # incomplete
            ("global_quantities/r0", np.nan),
            ("not/in/the/dd", [1.0, 2.0]),
            ("global_quantities", [1.0, 2.0]),  # structure
            ("global_quantities/ip", None),
        ],
    )
    def test_rejected(self, make_builder, path, value):
        builder = make_builder([1.0, 2.0])
        assert not builder.set(path, value, "x")
        assert not builder.filled

    def test_set_signal(self, make_builder):
        builder = make_builder([1.0])
        assert builder.set_signal("global_quantities/ip", [0.0, 2.0], [0.0, 4.0], "s")
        np.testing.assert_array_equal(builder.get("global_quantities/ip"), [2.0])
        assert not builder.set_signal("global_quantities/q_95", [2.0], [3.0], "s")

    def test_get_unfilled(self, make_builder):
        assert make_builder().get("global_quantities/ip") is None
