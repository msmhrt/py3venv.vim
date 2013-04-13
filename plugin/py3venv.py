#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

from ctypes import pythonapi
import os
import re
import site
import sys

RE_VENV_CFG = re.compile(r"""(?xa)
    \A\s*version\s*=\s*(?P<version>\S+)
""")


def get_venvcfg_path():
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path is None:
        return None

    venvcfg_path = os.path.join(venv_path, "pyvenv.cfg")
    return venvcfg_path


def get_venv_version(venvcfg_path):
    try:
        with open(venvcfg_path, encoding="utf-8") as venvcfg:
            for line in venvcfg:
                match = RE_VENV_CFG.match(line)
                if match is not None:
                    return match.groupdict().get("version")
    except OSError:
        pass

    return None


def get_venv_executable(venvcfg_path=None):
    if venvcfg_path is None:
        venvcfg_path = get_venvcfg_path()

    if venvcfg_path is None:
        return None

    py_version = "{0}.{1}.{2}".format(*sys.version_info)
    venv_version = get_venv_version(venvcfg_path)
    if py_version != venv_version:
        return None

    if sys.platform == "win32":
        bin_path = "Scripts"
        execfile = "Python.exe"
    else:
        bin_path = "bin"
        execfile = "python"

    venv_executable = os.path.abspath(os.path.join(venvcfg_path,
                                                   "..",
                                                   bin_path,
                                                   execfile))

    return venv_executable


def reset_syspath():
    # remove sys.__egginsert for easy-install.pth
    if hasattr(sys, "__egginsert"):
        delattr(sys, "__egginsert")

    saved_syspath = sys.path
    delattr(sys, "path")
    pythonapi.PySys_SetPath(pythonapi.Py_GetPath())
    saved_syspath[:] = sys.path
    sys.path = saved_syspath


def set_syspath(venv_executable=None):
    if venv_executable is None:
        venv_executable = get_venv_executable()

    if venv_executable is not None:
        sys.executable = venv_executable
        reset_syspath()
        site.main()
