#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

import io
import os
import sys
import unittest

from pep8 import StyleGuide


class TestPep8Style(unittest.TestCase):
    def test_pep8style(self):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.dirname(test_dir)
        pep8style = StyleGuide()

        saved_stdout, sys.stdout = sys.stdout, io.StringIO()
        try:
            pep8style.input_dir(dist_dir)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = saved_stdout

        report = pep8style.check_files()
        newline = os.linesep
        result_format = 'PEP8 failed (errors={:d}, warnings={:d})' + newline
        result = result_format.format(report.get_count('E'),
                                      report.get_count('W'))
        statistics = newline.join(report.get_statistics()) + newline
        message = newline.join((result, statistics, output))

        self.assertEqual(report.get_count(), 0, message)
