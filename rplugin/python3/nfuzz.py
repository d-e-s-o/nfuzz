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

from functools import (
  lru_cache,
)
from itertools import (
  islice,
)
from os.path import (
  dirname,
  expanduser,
)
from neovim import (
  api,
  function,
  plugin,
)
from re import (
  compile as regex,
)
from shlex import (
  split as shsplit,
)
from subprocess import (
  CalledProcessError,
  check_output,
  PIPE,
  Popen,
)


@plugin
class Main(object):
  # The default fuzzer command to use.
  DEFAULT_FUZZER = "fzy-tmux"
  # The default finder command to use.
  DEFAULT_FINDER = "fd --type=f ."

  # The name of the variable representing the fuzzer to invoke.
  FUZZER = "g:nfuzz_fuzzer"
  # The name of the variable representing the find command to invoke for
  # searching files.
  FINDER = "g:nfuzz_finder"

  # A regular expression for extracting the buffer name of Nvim's 'ls'
  # command.
  LS_REGEX = regex(".*\"(.+)\".*")


  def __init__(self, vim):
    """Initialize the plugin."""
    self.vim = vim


  @lru_cache()
  def variable(self, name, default):
    """Retrieve the value of the given variable."""
    try:
      return self.vim.command_output("echo %s" % name)
    except api.nvim.NvimError:
      return default


  def fuzzer(self):
    """Retrieve the fuzzer command to use."""
    return shsplit(self.variable(Main.FUZZER, Main.DEFAULT_FUZZER))


  def finder(self):
    """Retrieve the fuzzer command to use."""
    return shsplit(self.variable(Main.FINDER, Main.DEFAULT_FINDER))


  def iterBuffers(self):
    """Retrieve an iterator over all the available buffers."""
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
    return buffers


  @function("NfuzzBuffers", sync=False)
  def buffers(self, args):
    """Select a buffer to open by using 'fzy' on the output of Nvim's 'ls'."""
    buffers = map(lambda x: x.encode(), self.iterBuffers())
    buffers = b"\n".join(buffers)
    try:
      out = check_output(self.fuzzer(), input=buffers)
    except CalledProcessError as e:
      self.vim.command("echo \"%s\"" % str(e))
    else:
      self.vim.command("buffer %s" % out.decode())


  def cwd(self):
    """Retrieve the current working directory Nvim is in."""
    return self.vim.command_output("pwd").strip()


  @function("NfuzzFiles", sync=False)
  def files(self, args):
    """Select a file to open by using 'fzy' on the files below the source root directory."""
    # 'fd' does not understand '~' as the home directory, so we have to
    # expand that ourselves.
    dirs = map(expanduser, self.iterBuffers())
    dirs = map(dirname, dirs)
    dirs = filter(lambda x: len(x) > 0, dirs)
    dirs = list(set(dirs) | {self.cwd()})
    try:
      p1 = Popen(self.finder() + dirs, stdout=PIPE)
      p2 = Popen(self.fuzzer(), stdin=p1.stdout, stdout=PIPE)
      out, _ = p2.communicate()
    except CalledProcessError as e:
      self.vim.command("echo \"%s\"" % str(e))
    else:
      self.vim.command("edit %s" % out.decode())
