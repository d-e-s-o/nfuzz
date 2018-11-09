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
from os.path import (
  commonpath,
  dirname,
  expanduser,
  isabs,
  join,
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
  PIPE,
  Popen,
)


@plugin
class Main(object):
  # A regular expression for extracting the buffer name of Nvim's 'ls'
  # command.
  LS_REGEX = regex(".*\"(.+)\".*")


  def __init__(self, vim):
    """Initialize the plugin."""
    self.vim = vim


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
      out = check_output(["fzy-tmux"], input=buffers)
    except CalledProcessError as e:
      self.vim.command("echo \"%s\"" % str(e))
    else:
      self.vim.command("buffer %s" % out.decode())


  def cwd(self):
    """Retrieve the current working directory Nvim is in."""
    return self.vim.command_output("pwd").strip()


  def root(self):
    """Retrieve the directory root of all opened files.

      Neovim generally supports two modes of operation: One in which the
      current working directory is fixed and another one in which the
      editor always changes to the directory containing the file being
      edited. The more general approach is to be able to handle the
      second case and so that is what this function attempts to do.

      In a nutshell, we take the absolute paths to all already open
      files (i.e., buffers) and find the common prefix they all share.
    """
    def mkabs(path):
      """Make a path an absolute path."""
      # Buffer names may abbreviate the user's home directory, so make
      # sure to expand it.
      path = expanduser(path)

      if not isabs(path):
        path = join(cwd, path)

      return path

    cwd = self.cwd()
    paths = list(map(mkabs, self.iterBuffers()))
    if len(paths) == 1:
      return dirname(paths[0])
    else:
      return commonpath(list(paths))


  @function("NfuzzFiles", sync=False)
  def files(self, args):
    """Select a file to open by using 'fzy' on the files below the source root directory."""
    try:
      p1 = Popen(["fd", "--type=f", ".", self.root()], stdout=PIPE)
      p2 = Popen(["fzy-tmux"], stdin=p1.stdout, stdout=PIPE)
      out, _ = p2.communicate()
    except CalledProcessError as e:
      self.vim.command("echo \"%s\"" % str(e))
    else:
      self.vim.command("edit %s" % out.decode())
