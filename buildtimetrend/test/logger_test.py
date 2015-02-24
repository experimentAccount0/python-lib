# vim: set expandtab sw=4 ts=4:
#
# Unit tests for logger methods
#
# Copyright (C) 2014-2015 Dieter Adriaenssens <ruleant@users.sourceforge.net>
#
# This file is part of buildtimetrend/python-lib
# <https://github.com/buildtimetrend/python-lib/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import buildtimetrend
from buildtimetrend import set_loglevel
import unittest
import logging


class TestLogger(unittest.TestCase):
    def test_set_loglevel(self):
        logger = logging.getLogger(buildtimetrend.NAME)
        # test default loglevel
        self.assertEquals(logging.WARNING, logger.getEffectiveLevel())

        # test setting loglevel to INFO
        set_loglevel("INFO")
        self.assertEquals(logging.INFO, logger.getEffectiveLevel())

        # test setting loglevel to DEBUG
        set_loglevel("DEBUG")
        self.assertEquals(logging.DEBUG, logger.getEffectiveLevel())

        # test setting loglevel to ERROR
        set_loglevel("ERROR")
        self.assertEquals(logging.ERROR, logger.getEffectiveLevel())

        # test setting loglevel to CRITICAL
        set_loglevel("CRITICAL")
        self.assertEquals(logging.CRITICAL, logger.getEffectiveLevel())

        # test setting loglevel to WARNING
        set_loglevel("WARNING")
        self.assertEquals(logging.WARNING, logger.getEffectiveLevel())

        # error is thrown when called without parameters
        self.assertRaises(TypeError, set_loglevel)

        # error is thrown when called with an invalid parameter
        self.assertRaises(TypeError, set_loglevel, None)
        self.assertRaises(ValueError, set_loglevel, "invalid")

        # passing invalid tags should not change log level
        self.assertEquals(logging.WARNING, logger.getEffectiveLevel())
