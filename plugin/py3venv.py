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


def get_venv_prefix():
    return os.environ.get("VIRTUAL_ENV")


def is_venv_activated():
    # venv module has been added in Python 3.3
    if sys.version_info < (3, 3):
        return False

    activated = False
    if sys.platform == "win32" and sys.version_info < (3, 3, 3):
        # Because deactivate.bat in venv module of Python < 3.3.3 doesn't
        # unset %VIRTUAL_ENV% (see Issue #17744 on bugs.python.org)
        # we check %_OLD_VIRTUAL_PATH% instead of %VIRTUAL_ENV%.
        if os.environ.get("_OLD_VIRTUAL_PATH") is not None:
            activated = True
    elif get_venv_prefix() is not None:
        activated = True

    return activated


def make_pyvenv_cfg_path(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    try:
        pyvenv_cfg_path = os.path.join(venv_prefix, "pyvenv.cfg")
    except TypeError:
        pyvenv_cfg_path = None

    return pyvenv_cfg_path


def get_venv_original_prefix(venv_prefix=None):
    pyvenv_cfg_path = make_pyvenv_cfg_path(venv_prefix)
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


def make_distutils_path(prefix):
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
    distutils_path = make_distutils_path(prefix)
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


def get_venv_version(venv_prefix=None):
    original_prefix = get_venv_original_prefix(venv_prefix)
    if original_prefix is None:
        return None

    return get_python_version(original_prefix)


def is_valid_version(version):
    current_version = distutils.__version__
    if version != current_version:
        return False
    return True


def is_valid_lib_path(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return False

    try:
        lib_path = os.path.join(venv_prefix, LIB_PATH)
    except TypeError:
        return False

    return os.path.exists(lib_path)


def make_venv_executable_path(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    venv_executable_path = None
    try:
        venv_executable_path = os.path.abspath(os.path.join(venv_prefix,
                                                            BIN_PATH,
                                                            EXECFILE))
    except TypeError:
        pass

    return venv_executable_path


def reset_syspath():
    # remove sys.__egginsert for easy-install.pth
    if hasattr(sys, "__egginsert"):
        delattr(sys, "__egginsert")

    # id(sys.path) must not be changed.
    saved_syspath = sys.path
    try:
        from ctypes import pythonapi

        delattr(sys, "path")
        pythonapi.PySys_SetPath(pythonapi.Py_GetPath())
        saved_syspath[:] = sys.path
        error = None
    except (ImportError, AttributeError, OSError) as exception:
        error = exception
    finally:
        sys.path = saved_syspath

    return error


def get_vim_special_path():
    vim_special_path = None
    try:
        import vim

        if (vim.path_hook in sys.path_hooks and
                vim.VIM_SPECIAL_PATH in sys.path):
            vim_special_path = vim.VIM_SPECIAL_PATH
    except (AttributeError, ImportError):
        pass

    return vim_special_path


def activate_venv(venv_prefix=None, force=False):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    venv_version = get_venv_version(venv_prefix)
    if not (force or (is_valid_version(venv_version) and
                      is_venv_activated())):
        return None

    venv_executable_path = make_venv_executable_path(venv_prefix)
    if venv_executable_path is None:
        return None

    saved_sys_executable = sys.executable
    sys.executable = venv_executable_path
    vim_special_path = get_vim_special_path()

    error = reset_syspath()
    if error is not None:
        sys.executable = saved_sys_executable
        return None
    site.main()
    if vim_special_path is not None and vim_special_path not in sys.path:
        sys.path.append(vim_special_path)

    return venv_prefix


def get_orig_prefix_txt_path(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    try:
        orig_prefix_path = os.path.join(venv_prefix,
                                        LIB_PATH,
                                        "orig-prefix.txt")
    except TypeError:
        orig_prefix_path = None

    return orig_prefix_path


def get_virtualenv_original_prefix(venv_prefix=None):
    orig_prefix_txt_path = get_orig_prefix_txt_path(venv_prefix)
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


def get_virtualenv_version(venv_prefix=None):
    original_prefix = get_virtualenv_original_prefix(venv_prefix)
    if original_prefix is None:
        return None

    return get_python_version(original_prefix)


def get_virtualenv_activate_this_path(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    try:
        path = os.path.join(venv_prefix, BIN_PATH, "activate_this.py")
        virtualenv_activate_path = os.path.abspath(path)
    except TypeError:
        virtualenv_activate_path = None

    return virtualenv_activate_path


def activate_virtualenv(venv_prefix=None, force=False):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    virtualenv_version = get_virtualenv_version(venv_prefix)
    if not force and not is_valid_version(virtualenv_version):
        return None

    activate_this_path = get_virtualenv_activate_this_path(venv_prefix)
    if activate_this_path is None:
        return None

    new_venv_prefix = None
    try:
        # Using ISO/IEC 8859-1 just in case.
        with open(activate_this_path, encoding='iso8859-1') as activate_file:
            activate_source = activate_file.read()
        exec(activate_source, dict(__file__=activate_this_path))
        new_venv_prefix = venv_prefix
    except OSError:
        pass

    return new_venv_prefix


def activate(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    if not is_valid_lib_path(venv_prefix):
        return None

    new_venv_prefix = activate_venv(venv_prefix)
    if new_venv_prefix is None:
        new_venv_prefix = activate_virtualenv(venv_prefix)

    return new_venv_prefix
