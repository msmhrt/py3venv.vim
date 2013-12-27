#!/usr/bin/env python3
# vim:fileencoding=utf-8

# Copyright (c) 2013 Masami HIRATA <msmhrt@gmail.com>

from unittest import TestCase


class TestPy3venv(TestCase):
    def test_sys_attrs(self):
        from itertools import product
        import sys
        from plugin.py3venv import (fix_sys_attrs, recover_sys_attrs,
                                    AS_IS, NOT_FOUND)

        self.assertIs(fix_sys_attrs({"flags": AS_IS})["flags"], sys.flags)

        class ForTest:
            pass

        not_found = object()
        is_original = object()

        def counter():
            test_value = 0
            while True:
                yield test_value
                test_value += 1

        unique_value = counter()

        def _make_test_data(source):
            if source is object:
                test_data = object()
            elif type(source) is list or type(source) is dict:
                a_len = len(source)
                test_data = type(source)()
                for num in range(0, a_len):
                    if type(source) is list:
                        test_data.append(next(unique_value))
                    else:
                        key = next(unique_value)
                        test_data[key] = next(unique_value)
            else:
                test_data = source

            return test_data

        def _make_mock_sys(mock_sys, a_attr):
            backuped = None
            if a_attr is is_original:
                a_attr = getattr(mock_sys, "a", not_found)

            if a_attr is not_found:
                if hasattr(mock_sys, "a"):
                    delattr(mock_sys, "a")
            else:
                a_attr = _make_test_data(a_attr)
                setattr(mock_sys, "a", a_attr)
                backuped = {"id": a_attr, "value": a_attr}
                if type(a_attr) is list or type(a_attr) is dict:
                    backuped["value"] = a_attr.copy()

            return backuped

        original_attrs = (not_found, object, None, 1, [], {}, [2, 3], {4: 5})
        modified_attrs = (is_original, not_found, object, None, 1, [], {},
                          [2, 3], {4: 5})
        new_attrs = (AS_IS, NOT_FOUND, is_original, object, None, (), [], {},
                     [6, 7], {8: 9})

        for ((count_original, a_original),
             (count_modified, a_modified),
             (count_new, a_new)) in product(enumerate(original_attrs, 1),
                                            enumerate(modified_attrs, 1),
                                            enumerate(new_attrs, 1)):
            test_id = "#{},{},{}".format(count_original,
                                         count_modified,
                                         count_new)

            mock_sys = ForTest()
            backuped = _make_mock_sys(mock_sys, a_original)

            # make a new_sys_attrs
            if a_new is a_original:
                continue
            elif a_new is is_original:
                if not hasattr(mock_sys, "a"):
                    continue
                a_new = getattr(mock_sys, "a")
            else:
                a_new = _make_test_data(a_new)
            new_sys_attrs = {"a": a_new}

            # call fix_sys_attrs()
            saved_attrs = fix_sys_attrs(new_sys_attrs, sys=mock_sys)

            # check the the return value of fix_sys_attrs()
            saved_attr = saved_attrs["a"]
            if a_original is not_found:
                self.assertIs(saved_attr, NOT_FOUND, msg=test_id)
            elif type(saved_attr) is list:
                self.assertEqual(len(saved_attr), 3, msg=test_id)
                self.assertIs(saved_attr[0], AS_IS, msg=test_id)
                self.assertIs(saved_attr[1], backuped["id"], msg=test_id)
                self.assertEqual(saved_attr[2], backuped["value"],
                                 msg=test_id)
            else:
                self.assertIs(saved_attr, backuped["id"], msg=test_id)
                self.assertEqual(saved_attr, backuped["value"],
                                 msg=test_id)

            # check the mock_sys after fix_sys_attrs()
            dummy = object()
            new_attr = getattr(mock_sys, "a", dummy)
            if a_new is NOT_FOUND or (a_new is AS_IS and backuped is None):
                self.assertIs(new_attr, dummy, msg=test_id)
                self.assertFalse(hasattr(mock_sys, "a"), msg=test_id)
            elif a_new is AS_IS:
                self.assertIs(new_attr, backuped["id"], msg=test_id)
            elif ((type(a_new) is list and type(a_original) is list) or
                  (type(a_new) is dict and type(a_original) is dict)):
                self.assertIs(new_attr, backuped["id"], msg=test_id)
                self.assertEqual(new_attr, a_new, msg=test_id)
            else:
                self.assertIs(new_attr, a_new, msg=test_id)

            # modify the mock_sys
            _make_mock_sys(mock_sys, a_modified)

            # call recover_sys_attrs()
            recover_sys_attrs(saved_attrs, sys=mock_sys)

            # check the mock_sys after recover_sys_attrs()
            original_attr = getattr(mock_sys, "a", not_found)
            if original_attr is not_found:
                self.assertIs(backuped, None, msg=test_id)
                self.assertIs(original_attr, not_found, msg=test_id)
            else:
                self.assertIs(original_attr, backuped["id"], msg=test_id)
                self.assertEqual(original_attr, backuped["value"], msg=test_id)
