#!/usr/bin/env python

#/***************************************************************************
# *   Copyright (C) 2022 Daniel Mueller (deso@posteo.net)                   *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation, either version 3 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU General Public License for more details.                          *
# *                                                                         *
# *   You should have received a copy of the GNU General Public License     *
# *   along with this program.  If not, see <http://www.gnu.org/licenses/>. *
# ***************************************************************************/

"""Tests for the nfuzz neovim plugin."""

from rplugin.python3.nfuzz import (
  removeSubsumedPaths,
)
from unittest import (
  main,
  TestCase,
)


class TestNfuzz(TestCase):
  """Tests for chosen bits of the nfuzz functionality."""
  def testSubsumedPathRemovalAbsolute(self):
    """Verify that our logic to remove subsumed paths works as expected on absolute paths."""
    paths = [
      "/rplugin",
      "/rplugin/python3/test",
      "/rplugin/python3",
    ]

    non_subsumed = removeSubsumedPaths(paths)
    self.assertEqual(non_subsumed, ["/rplugin"])


  def testSubsumedPathRemovalRelative(self):
    """Verify that our logic to remove subsumed paths works as expected on relative paths."""
    paths = [
      "./rplugin/python3/test",
      "./rplugin",
      "./rplugin/python3",
    ]

    non_subsumed = removeSubsumedPaths(paths)
    self.assertEqual(non_subsumed, ["./rplugin"])


  def testSubsumedPathRemovalRelativeWithoutLeadingDot(self):
    """
    Verify that our logic to remove subsumed paths works as expected on relative paths without a
    leading dot.
    """
    paths = [
      "rplugin/python3/test",
      "rplugin",
      "rplugin/python3",
    ]

    non_subsumed = removeSubsumedPaths(paths)
    self.assertEqual(non_subsumed, ["rplugin"])


  def testSubsumedPathRemovalMixed(self):
    """Verify that our logic to remove subsumed paths works as expected on mixed paths."""
    paths = [
      "/rplugin",
      "./rplugin/python3/test",
      "/rplugin/python3",
    ]

    non_subsumed = removeSubsumedPaths(paths)
    self.assertEqual(non_subsumed, ["./rplugin/python3/test", "/rplugin"])


if __name__ == "__main__":
  main()
