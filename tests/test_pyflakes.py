#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

import os
from subprocess import check_output, CalledProcessError, STDOUT
import sys
from unittest import TestCase


class TestPyflakes(TestCase):
    def test_pyflakes(self):
        if sys.platform == "win32":
            encoding = "mbcs"
        else:
            encoding = "utf-8"

        test_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.dirname(test_dir)
        os.environ["PYFLAKES_NODOCTEST"] = "1"

        try:
            pyflakes_output = check_output(["pyflakes", dist_dir],
                                           stderr=STDOUT).decode(encoding)
        except CalledProcessError as exception:
            pyflakes_output = exception.output.decode(encoding)
        message = "\n" + pyflakes_output.replace("\r\n",
                                                 "\n").replace("\r", "\n")
        self.assertEqual(len(pyflakes_output), 0, msg=message)
