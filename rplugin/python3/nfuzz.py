# nfuzz.py

#/***************************************************************************
# *   Copyright (C) 2018 Daniel Mueller (deso@posteo.net)                   *
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

from itertools import (
  islice,
)
from neovim import (
  function,
  plugin,
)
from re import (
  compile as regex,
)
from subprocess import (
  CalledProcessError,
  check_output,
)


@plugin
class Main(object):
  # A regular expression for extracting the buffer name of Nvim's 'ls'
  # command.
  LS_REGEX = regex(".*\"(.+)\".*")


  def __init__(self, vim):
    """Initialize the plugin."""
    self.vim = vim


  @function("NfuzzBuffers", sync=False)
  def buffers(self, args):
    """Select a buffer to open by using 'fzy' on the output of Nvim's 'ls'."""
    def filterBufs(line):
      """Filter out the buffer names from the output of 'ls'."""
      m = Main.LS_REGEX.match(line)
      buf, = m.groups()
      return buf

    buffers = self.vim.command_output("ls").splitlines()
    # Remove the first line of the output.
    buffers = islice(buffers, 1, None)
    # Then extract the actual buffer names.
    buffers = map(filterBufs, buffers)
    buffers = map(lambda x: x.encode(), buffers)
    buffers = b"\n".join(buffers)

    try:
      out = check_output(["fzy-tmux"], input=buffers)
    except CalledProcessError as e:
      self.vim.command("echo \"%s\"" % str(e))
    else:
      self.vim.command("buffer %s" % out.decode())
