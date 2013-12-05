" py3venv.vim - Vim global plugin to support Python 3 venv

" Version:      0.2
" Last Change:  3 Dec 2013
" Maintainer:   Masami HIRATA <msmhrt@gmail.com>
" License:      BSD 2-Clause License

if !has('python3')
  echomsg "Error: Required vim compiled with +python3"
  finish
endif

if exists("g:loaded_py3venv")
  finish
endif
let g:loaded_py3venv = 1

let s:save_cpo = &cpo
set cpo&vim

python3 << PYTHONEOF
try:
    class DummyClassForLocalScope():
        import os
        import sys
        import vim

        plugin_path = vim.eval('expand("<sfile>:p:h")')
        sys.path.insert(0, plugin_path)
        import py3venv

        # remove plugin_path from sys.path before py3env.activate()
        if plugin_path in sys.path:
            sys.path.remove(plugin_path)

        py3venv.activate()

        raise RuntimeError
except RuntimeError:
    pass
PYTHONEOF

let &cpo = s:save_cpo
unlet s:save_cpo
