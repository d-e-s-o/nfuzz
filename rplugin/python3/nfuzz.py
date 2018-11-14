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
from os.path import (
  dirname,
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
  TimeoutExpired,
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
    return map(lambda x: x.name, self.vim.request("nvim_list_bufs"))


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


  def pipeline(self, cmd1, cmd2):
    """Invoke a pipeline of two commands."""
    with Popen(cmd1, stdout=PIPE, stderr=PIPE) as p1,\
        Popen(cmd2, stdin=p1.stdout, stdout=PIPE, stderr=PIPE) as p2:
      # Allow 'p1' to receive a SIGPIPE if 'p2' exits.
      p1.stdout.close()
      p1.stdout = None

      _, err = p1.communicate()
      if p1.returncode != 0:
        p2.terminate()
        try:
          p2.wait(2)
        except TimeoutExpired:
          p2.kill()

        raise CalledProcessError(p1.returncode, p1.args, output=err)

      out, err = p2.communicate()
      if p2.returncode != 0:
        raise CalledProcessError(p2.returncode, p2.args, output=err)

      return out


  @function("NfuzzFiles", sync=False)
  def files(self, args):
    """Select a file to open by using 'fzy' on the files below the source root directory."""
    # TODO: 'fd' fails if a directory does not exist. As a useful
    #       pre-processing step minimizing such failures we should
    #       remove subsumed directories.
    dirs = map(dirname, self.iterBuffers())
    dirs = filter(lambda x: len(x) > 0, dirs)
    dirs = list(set(dirs) | {self.cwd()})
    try:
      out = self.pipeline(self.finder() + dirs, self.fuzzer())
    except CalledProcessError as e:
      self.vim.command("echo \"%s: %s\"" % (str(e), e.output.decode()))
    else:
      self.vim.command("edit %s" % out.decode())
