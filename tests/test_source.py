#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

import os
import unittest

import regex

IGNORED_DIRS = {
    '__pycache__', 'CVS', '.bzr', '.git', '.hg', '.svn'}
IGNORED_FILES = {}
LINE_SHEBANG = "#!/usr/bin/env python3"
LINE_ENCODING = "# vim:fileencoding=utf-8"
ERROR_SHEBANG = "{filepath}:{shebang_line_no} does not contain a valid shebang"
ERROR_ENCODING = ("{filepath}:{encoding_line_no} does not contain " +
                  "a valid encoding declaration")
ERROR_COPYRIGHT = "{filepath}: does not contain a valid copyright"
AUTHORS = ("Masami HIRATA <msmhrt@gmail.com>",)
RESTR_AUTHORS = ("(?:" +
                 "|".join([regex.escape(author) for author in AUTHORS]) +
                 ")")
RESTR_COPYRIGHT_LINE = r"""(?x)
    \#\ Copyright\ \(c\)\ 20[0-9][0-9](?:-20[0-9][0-9])?
    \ {RESTR_AUTHORS}"""
RE_COPYRIGHT = regex.compile(RESTR_COPYRIGHT_LINE.format(**locals()))


class TestSourceCode(unittest.TestCase):
    def test_source_code(self):
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.dirname(tests_dir)
        for dirpath, dirnames, filenames in os.walk(dist_dir):
            if os.path.basename(dirpath) in IGNORED_DIRS:
                continue
            for filename in filenames:
                if (not filename.endswith('.py')
                        or filename in IGNORED_FILES):
                    continue
                filepath = os.path.join(dirpath, filename)
                if (filename == '__init__.py' and
                        os.path.getsize(filepath) == 0):
                    continue
                self._check_file(filepath)

    def _check_file(self, filepath):
        with open(filepath, encoding='utf-8') as file:
            line_no = 1
            shebang = file.readline().rstrip("\n")
            shebang_line_no = line_no
            if shebang.startswith("#!"):
                encoding = file.readline().rstrip("\n")
                line_no += 1
            else:
                encoding = shebang
            encoding_line_no = line_no
            self.assertEqual(shebang, LINE_SHEBANG,
                             ERROR_SHEBANG.format(**locals()))
            self.assertEqual(encoding, LINE_ENCODING,
                             ERROR_ENCODING.format(**locals()))
            copyright_line_no = 0
            for line_no, line in enumerate(file.readlines(), start=line_no):
                line = line.rstrip("\n")
                if RE_COPYRIGHT.fullmatch(line) is not None:
                    copyright_line_no = line_no
                    break
            self.assertNotEqual(0,
                                copyright_line_no,
                                ERROR_COPYRIGHT.format(**locals()))
