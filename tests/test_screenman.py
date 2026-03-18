#!/usr/bin/env python

"""Tests for `screenman` package."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from screenman import cli
from screenman.screen import Mode, Screen, find_internal_external, apply_mirror


def _make_screen(name, modes=None, edid_hex=""):
    """Helper to create a Screen with given name and modes."""
    if modes is None:
        modes = [Mode(1920, 1080, 60.0, current=True, preferred=True)]
    return Screen(name, False, None, modes, edid_hex)


class TestFindInternalExternal:
    def test_classifies_edp_as_internal(self):
        edp = _make_screen("eDP-1")
        hdmi = _make_screen("HDMI-1")
        dp = _make_screen("DP-1")
        internal, externals = find_internal_external([edp, hdmi, dp])
        assert internal is edp
        assert externals == [hdmi, dp]

    def test_no_internal(self):
        hdmi = _make_screen("HDMI-1")
        internal, externals = find_internal_external([hdmi])
        assert internal is None
        assert externals == [hdmi]

    def test_no_external(self):
        edp = _make_screen("eDP-1")
        internal, externals = find_internal_external([edp])
        assert internal is edp
        assert externals == []

    def test_empty(self):
        internal, externals = find_internal_external([])
        assert internal is None
        assert externals == []


class TestBuildCmdScaleSameAs:
    def test_scale_flag(self):
        s = _make_screen("eDP-1")
        s.scale = (1.5, 1.25)
        cmd = s.build_cmd()
        assert cmd is not None
        assert "--scale" in cmd
        idx = cmd.index("--scale")
        assert cmd[idx + 1] == "1.5x1.25"

    def test_same_as_flag(self):
        s = _make_screen("eDP-1")
        s.same_as = "HDMI-1"
        cmd = s.build_cmd()
        assert cmd is not None
        assert "--same-as" in cmd
        idx = cmd.index("--same-as")
        assert cmd[idx + 1] == "HDMI-1"

    def test_no_scale_when_not_set(self):
        s = _make_screen("eDP-1")
        s.is_primary = True  # trigger a change so build_cmd returns something
        cmd = s.build_cmd()
        assert cmd is not None
        assert "--scale" not in cmd
        assert "--same-as" not in cmd


class TestApplyMirror:
    def test_basic_mirror(self):
        # Use different current vs preferred so resolution setter triggers --mode
        int_modes = [
            Mode(1920, 1080, 60.0, current=True, preferred=True),
        ]
        ext_modes = [
            Mode(1920, 1080, 60.0, current=True, preferred=False),
            Mode(3840, 2160, 60.0, current=False, preferred=True),
        ]
        internal = _make_screen("eDP-1", int_modes)
        external = _make_screen("HDMI-1", ext_modes)

        with patch("screenman.screen.exec_cmd") as mock_exec:
            mock_exec.return_value = []
            apply_mirror([internal, external])

            mock_exec.assert_called_once()
            cmd = mock_exec.call_args[0][0]
            assert "xrandr" == cmd[0]
            # External should have --mode and --pos
            assert "--mode" in cmd
            assert "3840x2160" in cmd
            assert "--pos" in cmd
            assert "0x0" in cmd
            # Internal should have --scale and --same-as
            assert "--scale" in cmd
            assert "2.0x2.0" in cmd
            assert "--same-as" in cmd
            assert "HDMI-1" in cmd

    def test_no_internal_raises(self):
        external = _make_screen("HDMI-1")
        with pytest.raises(RuntimeError, match="No internal"):
            apply_mirror([external])

    def test_no_external_raises(self):
        internal = _make_screen("eDP-1")
        with pytest.raises(RuntimeError, match="No external"):
            apply_mirror([internal])

    def test_no_preferred_mode_raises(self):
        int_modes = [Mode(1920, 1080, 60.0, current=True, preferred=True)]
        ext_modes = [Mode(1920, 1080, 60.0, current=True, preferred=False)]
        internal = _make_screen("eDP-1", int_modes)
        external = _make_screen("HDMI-1", ext_modes)

        with pytest.raises(RuntimeError, match="No preferred mode"):
            apply_mirror([internal, external])

    def test_multiple_externals_disables_extras(self):
        int_modes = [Mode(1920, 1080, 60.0, current=True, preferred=True)]
        ext_modes = [Mode(2560, 1440, 60.0, current=True, preferred=True)]
        internal = _make_screen("eDP-1", int_modes)
        ext1 = _make_screen("HDMI-1", ext_modes)
        ext2 = _make_screen("DP-1", ext_modes)

        with patch("screenman.screen.exec_cmd") as mock_exec:
            mock_exec.return_value = []
            apply_mirror([internal, ext1, ext2])

            cmd = mock_exec.call_args[0][0]
            # ext2 (DP-1) should be turned off
            assert "--off" in cmd


class TestCliMirrorFlags:
    def test_mirror_and_mirror_off_mutual_exclusion(self):
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--mirror", "--mirror-off"])
        assert result.exit_code != 0
        assert "Cannot use --mirror and --mirror-off together" in result.output

    def test_help_shows_mirror_flags(self):
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--help"])
        assert "--mirror" in result.output
        assert "--mirror-off" in result.output
