#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

import distutils
import os
import re
import site
import sys

if sys.platform == "win32":
    BIN_PATH = "Scripts"
    LIB_PATH = "Lib"
    EXECFILE = "Python.exe"
else:
    BIN_PATH = "bin"
    LIB_PATH = os.path.join("lib",
                            "python{0}.{1}".format(*sys.version_info))
    EXECFILE = "python"

RE_VENV_HOME = re.compile(r"""(?xa)
    \A\s*home\s*=\s*(?P<home>[^\r\n]+)""")
RE_PYTHON_VERSION = re.compile(r"""(?xa)
    \A\s*__version__\s*=\s*\"(?P<version>[^"]+)\"""")


def get_venv_path():
    return os.environ.get("VIRTUAL_ENV")


def get_pyvenv_cfg_path(venv_path=None):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    try:
        pyvenv_cfg_path = os.path.join(venv_path, "pyvenv.cfg")
    except TypeError:
        pyvenv_cfg_path = None

    return pyvenv_cfg_path


def get_venv_original_prefix(venv_path=None):
    pyvenv_cfg_path = get_pyvenv_cfg_path(venv_path)
    if pyvenv_cfg_path is None:
        return None

    original_prefix = None
    try:
        # 'pyvenv.cfg' is written in UTF-8
        with open(pyvenv_cfg_path, encoding='utf-8') as pyvenv_cfg_file:
            for line in pyvenv_cfg_file:
                match = RE_VENV_HOME.match(line)
                if match is not None:
                    original_prefix = match.groupdict().get("home")
                    break
    except OSError:
        pass

    if original_prefix is not None and sys.platform != "win32":
        # /original/prefix/bin -> /original/prefix
        original_prefix = os.path.dirname(original_prefix)
    return original_prefix


def get_distutils_path(prefix):
    if prefix is None:
        return None

    try:
        distutils_path = os.path.join(prefix,
                                      LIB_PATH,
                                      "distutils",
                                      "__init__.py")
    except TypeError:
        distutils_path = None

    return distutils_path


def get_python_version(prefix):
    distutils_path = get_distutils_path(prefix)
    if distutils_path is None:
        return None

    python_version = None
    try:
        # Using ISO/IEC 8859-1 just in case.
        with open(distutils_path, encoding='iso8859-1') as distutils_file:
            for line in distutils_file:
                match = RE_PYTHON_VERSION.match(line)
                if match is not None:
                    python_version = match.groupdict().get("version")
    except OSError:
        pass

    return python_version


def get_venv_version(venv_path=None):
    original_prefix = get_venv_original_prefix(venv_path)
    if original_prefix is None:
        return None

    return get_python_version(original_prefix)


def is_valid_version(version):
    current_version = distutils.__version__
    if version == current_version:
        return True
    return False


def get_venv_executable(venv_path=None):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    venv_executable = None
    try:
        venv_executable = os.path.abspath(os.path.join(venv_path,
                                                       BIN_PATH,
                                                       EXECFILE))
    except TypeError:
        pass

    return venv_executable


def reset_syspath():
    from ctypes import pythonapi

    # remove sys.__egginsert for easy-install.pth
    if hasattr(sys, "__egginsert"):
        delattr(sys, "__egginsert")

    # id(sys.path) must not be changed.
    saved_syspath = sys.path
    delattr(sys, "path")
    pythonapi.PySys_SetPath(pythonapi.Py_GetPath())
    saved_syspath[:] = sys.path
    sys.path = saved_syspath


def activate_venv(venv_path=None, force=False):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    venv_version = get_venv_version(venv_path)
    if not force and not is_valid_version(venv_version):
        return None

    venv_executable = get_venv_executable(venv_path)
    if venv_executable is None:
        return None

    saved_sys_executable = sys.executable
    sys.executable = venv_executable
    try:
        reset_syspath()
        site.main()
    except (ImportError, AttributeError, OSError):
        sys.executable = saved_sys_executable
        return None

    return venv_path


def get_orig_prefix_txt_path(venv_path=None):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    try:
        orig_prefix_path = os.path.join(venv_path,
                                        LIB_PATH,
                                        "orig-prefix.txt")
    except TypeError:
        orig_prefix_path = None

    return orig_prefix_path


def get_virtualenv_original_prefix(venv_path=None):
    orig_prefix_txt_path = get_orig_prefix_txt_path(venv_path)
    if orig_prefix_txt_path is None:
        return None

    original_prefix = None
    try:
        # 'orig-prefix.txt' is written in UTF-8
        with open(orig_prefix_txt_path,
                  encoding='utf-8') as orig_prefix_txt_file:
            original_prefix = orig_prefix_txt_file.readline()
    except OSError:
        pass

    return original_prefix


def get_virtualenv_version(venv_path=None):
    original_prefix = get_virtualenv_original_prefix(venv_path)
    if original_prefix is None:
        return None

    return get_python_version(original_prefix)


def get_virtualenv_activate_this_path(venv_path=None):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    try:
        path = os.path.join(venv_path, BIN_PATH, "activate_this.py")
        virtualenv_activate_path = os.path.abspath(path)
    except TypeError:
        virtualenv_activate_path = None

    return virtualenv_activate_path


def activate_virtualenv(venv_path=None, force=False):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    virtualenv_version = get_virtualenv_version(venv_path)
    if not force and not is_valid_version(virtualenv_version):
        return None

    activate_this_path = get_virtualenv_activate_this_path(venv_path)
    if activate_this_path is not None:
        try:
            activate_source = open(activate_this_path).read()
            exec(activate_source, dict(__file__=activate_this_path))
        except OSError:
            pass
        else:
            return venv_path


def set_syspath(venv_path=None):
    if venv_path is None:
        venv_path = get_venv_path()
        if venv_path is None:
            return None

    status = activate_venv(venv_path)
    if status is not None:
        return status

    status = activate_virtualenv(venv_path)
    if status is not None:
        return status

    return None
