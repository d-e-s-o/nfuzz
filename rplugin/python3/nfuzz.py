# nfuzz.py

#/***************************************************************************
# *   Copyright (C) 2018-2022 Daniel Mueller (deso@posteo.net)              *
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
  chain,
)
from os import (
  getcwd,
)
from os.path import (
  abspath,
  commonpath,
  dirname,
  isdir,
  join,
  relpath,
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


def removeSubsumedPaths(paths):
  """Remove paths that are subsumed by directories."""
  if len(paths) <= 1:
    return paths

  # We work on a sorted list of paths. This way we are sure that
  # paths potentially subsuming other paths appear before the latter.
  paths = sorted(paths)
  subsumer, *paths = paths
  new_paths = [subsumer]

  for path in paths:
    common = commonpath([abspath(subsumer), abspath(path)])
    if common != abspath(subsumer):
      # `subsumer` does not subsume `path`. Add it to the new list of
      # paths.
      new_paths += [path]
      subsumer = path

  return new_paths


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
    """Retrieve the finder command to use."""
    return shsplit(self.variable(Main.FINDER, Main.DEFAULT_FINDER))


  def iterBuffers(self):
    """Retrieve an iterator over all the available buffers."""
    return map(lambda x: x.name, self.vim.api.list_bufs())


  @function("NfuzzBuffers", sync=False)
  def buffers(self, args):
    """Select a buffer to open by using 'fzy' on the output of Nvim's 'ls'."""
    cwd = self.cwd()
    buffers = self.iterBuffers()
    buffers = map(lambda x: relpath(x, cwd), buffers)
    buffers = map(lambda x: x.encode(), buffers)
    buffers = b"\n".join(buffers)
    try:
      out = check_output(self.fuzzer(), input=buffers)
    except CalledProcessError as e:
      self.vim.command("echo \"%s\"" % str(e))
    else:
      # Output may be empty if the user aborted the fuzzer invocation,
      # for example, in which case we want to do nothing.
      if out:
        self.vim.command("buffer %s" % abspath(join(cwd, out.decode())))


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
    dirs = map(dirname, self.iterBuffers())
    dirs = filter(lambda x: len(x) > 0, dirs)
    dirs = list(chain(dirs, [getcwd()]))
    dirs = filter(isdir, dirs)
    dirs = map(abspath, dirs)
    dirs = removeSubsumedPaths(list(dirs))
    try:
      out = self.pipeline(self.finder() + dirs, self.fuzzer())
    except CalledProcessError as e:
      self.vim.command("echo \"%s: %s\"" % (str(e), e.output.decode()))
    else:
      self.vim.command("edit %s" % out.decode())
