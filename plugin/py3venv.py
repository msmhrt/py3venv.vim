#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

import distutils
import os
import re
import sys

if sys.platform == "win32":
    BIN_PATH = "Scripts"
    LIB_PATH = "Lib"
else:
    BIN_PATH = "bin"
    LIB_PATH = os.path.join("lib",
                            "python{0}.{1}".format(*sys.version_info))

AS_IS = object()
NOT_FOUND = object()

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
    except EnvironmentError:
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
    except EnvironmentError:
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

    return os.path.isdir(lib_path)


def make_prognames():
    if sys.platform == "win32":
        prognames = ["python.exe"]
    else:
        prognames = ["python",
                     "python{0}".format(*sys.version_info),
                     "python{0}.{1}".format(*sys.version_info)]
        # for future use
        if (hasattr(sys, "abiflags") and
                sys.abiflags is not None and sys.abiflags != ""):
            prognames.append("python{0}.{1}".format(*sys.version_info) +
                             sys.abiflags)
    return prognames


def make_venv_executable_path(venv_prefix=None):
    if venv_prefix is None:
        venv_prefix = get_venv_prefix()
        if venv_prefix is None:
            return None

    venv_executable_path = None
    try:
        for progname in make_prognames():
            path = os.path.join(venv_prefix, BIN_PATH, progname)
            path = os.path.abspath(path)
            if os.path.isfile(path):
                venv_executable_path = path
                break
    except TypeError:
        pass

    return venv_executable_path


def reset_syspath():
    # id(sys.path) must not be changed.
    original_syspath = sys.path
    try:
        from ctypes import pythonapi

        # Delete sys.path before calling PySys_SetPath()
        delattr(sys, "path")

        # All preparations are finished, Now we will call Py_GetPath()
        p_module_search_path = pythonapi.Py_GetPath()

        # Reset sys.path
        pythonapi.PySys_SetPath(p_module_search_path)

        # id(sys.path) must not be changed.
        original_syspath[:] = sys.path

        error = None
    except (ImportError, AttributeError, EnvironmentError) as exception:
        error = exception

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


def fix_sys_attrs(new_sys_attrs, sys=sys):
    saved_sys_attrs = {}
    for attr_name in new_sys_attrs:
        original_attr = getattr(sys, attr_name, NOT_FOUND)
        new_attr = new_sys_attrs[attr_name]

        if type(original_attr) is list:
            saved_sys_attrs[attr_name] = [AS_IS,
                                          original_attr,
                                          original_attr[:]]
        elif type(original_attr) is dict:
            saved_sys_attrs[attr_name] = [AS_IS,
                                          original_attr,
                                          original_attr.copy()]
        else:
            saved_sys_attrs[attr_name] = original_attr

        if original_attr is new_attr or new_attr is AS_IS:
            pass
        elif new_attr is NOT_FOUND:
            # original_attr isn't NOT_FOUND because original_attr
            # isn't new_attr
            delattr(sys, attr_name)
        elif type(original_attr) is list and type(new_attr) is list:
            original_attr[:] = new_attr
        elif type(original_attr) is dict and type(new_attr) is dict:
            original_attr.clear()
            original_attr.update(new_attr)
        else:
            setattr(sys, attr_name, new_attr)

    return saved_sys_attrs


def recover_sys_attrs(saved_sys_attrs, sys=sys):
    for attr_name in saved_sys_attrs:
        fixed_attr = getattr(sys, attr_name, NOT_FOUND)
        saved_attr = saved_sys_attrs[attr_name]
        if fixed_attr is saved_attr:
            pass
        elif saved_attr is NOT_FOUND:
            delattr(sys, attr_name)
        elif type(saved_attr) is list:
            if (len(saved_attr) != 3 or saved_attr[0] is not AS_IS or
                    (type(saved_attr[1]) is not list and
                     type(saved_attr[1]) is not dict) or
                    saved_attr[1].__class__ is not saved_attr[2].__class__):
                print("Can't restore {} to sys.{}".format(saved_attr,
                                                          attr_name),
                      file=sys.stderr)
                continue

            if fixed_attr is not saved_attr[1]:
                setattr(sys, attr_name, saved_attr[1])
                fixed_attr = saved_attr[1]

            if type(fixed_attr) is list:
                fixed_attr[:] = saved_attr[2]
            elif type(fixed_attr) is dict:
                fixed_attr.clear()
                fixed_attr.update(saved_attr[2])
        else:
            setattr(sys, attr_name, saved_attr)


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

    # Fix attributes in sys module
    new_sys_attrs = {"__egginsert": NOT_FOUND,
                     "_home": NOT_FOUND,
                     "executable": venv_executable_path,
                     "modules": AS_IS,
                     "path": AS_IS}
    saved_sys_attrs = fix_sys_attrs(new_sys_attrs)

    # Save vim_special_path before calling reset_syspath()
    vim_special_path = get_vim_special_path()

    error = reset_syspath()
    if error is not None:
        recover_sys_attrs(saved_sys_attrs)
        return None

    # Call main() of site module in new module search path
    try:
        if "site" in sys.modules:
            del(sys.modules["site"])
        import site
        site.main()
    except ImportError:
        recover_sys_attrs(saved_sys_attrs)
        return None

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
    except EnvironmentError:
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
    except EnvironmentError:
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
