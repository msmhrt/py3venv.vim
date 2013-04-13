" py3venv.vim - Vim global plugin to support Python 3 venv

" Version:      0.1
" Last Change:  13 Apr 2013
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
import os
import sys
import vim

sys.path.insert(0,
		os.path.join(vim.eval('expand("<sfile>:p:h:h")'),
		'plugin'))
import py3venv
py3venv.set_syspath()

PYTHONEOF

let &cpo = s:save_cpo
unlet s:save_cpo
