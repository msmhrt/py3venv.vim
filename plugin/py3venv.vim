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

        py3venv_path = os.path.join(vim.eval('expand("<sfile>:p:h:h")'),
                                    'plugin')
        sys.path.insert(0, py3venv_path)
        import py3venv
        status = py3venv.set_syspath()
        if status is not None and py3venv_path in sys.path:
            sys.path.remove(py3venv_path)

        raise RuntimeError
except RuntimeError:
    pass
PYTHONEOF

let &cpo = s:save_cpo
unlet s:save_cpo
