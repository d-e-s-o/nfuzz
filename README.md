nfuzz
=====

**nfuzz** is a [`Neovim`][neovim] plugin that enables fuzzy search on
certain operations. A typical example is selecting a buffer to display
in the current window. There are multiple ways to open a buffer: if the
buffer number is known it can be opened directly via `:b <nr>`. Given
that this is unlikely for all but the most often referenced buffers, a
common alternative is to use `Neovim`'s buffer name auto completion. As
long as the sequence typed by the user uniquely identifies a buffer,
`Neovim` will be able to open it. Even in such a case, though, the
sequence must represent a contiguous part of the buffer's path, a
property hard to achieve once many open buffers exist and files have
identical names.

A common solution to problems like this is the application of fuzzy
searching. Fuzzy search describes a search where the character the user
typed are searched for in the input list, but the only constraint is
that they those characters appear in the result in order they were
supplied. Most importantly, the user is not required to supply a
contiguous part of the intended result. For example, the search string
`fzy` would match <tt><b>f</b>u<b>z</b>z<b>y</b></tt>, `abc` could match
<tt><b>a</b>nother <b>b</b>eautiful <b>c</b>loud</tt>, or `check` could
match <tt><b>check</b>_output</tt>.

The **nfuzz** plugin brings fuzzy search to `Neovim`!


Installation
------------

Installation typically happens by means of a plugin manager. For
[`Vundle`][vundle] the configuration could look like this:
```vim
call vundle#begin('~/.config/nvim/bundle')
...
Plugin 'd-e-s-o/nfuzz' "<---- relevant line
...
call vundle#end()
```

To actually pull the plugin run `:PluginInstall`. Please adjust the
above in accordance with the plugin manager you use.

Since most plugin managers are oblivious to the fact that they are
use in conjunction with `Neovim`, and `Neovim` requires the creation of
a manifest for all "remote" plugins, an additional command should be run
after a restart of the editor:
```vim
:UpdateRemotePlugins
```

By default **nfuzz** uses [`fzy`][fzy] to facilitate the fuzzy search
and [`fd`][fd] to find files. See below for how to change those
defaults.


Configuration
-------------

As is common for plugins, **nfuzz** exposes a set of functions providing
its core functionality and users should define key bindings to invoke
them. A sample configuration may look like this:
```vim
map <leader>b :call NfuzzBuffers()<CR>
map <leader>f :call NfuzzFiles()<CR>
```

In addition, the default fuzzy searcher as well as the program to find
files can be configured through global variables:
```vim
" The fuzzy searcher to use.
let g:nfuzz_fuzzer = "fzy-tmux"
" The command to list all files below a set of directories.
let g:nfuzz_finder = "fd --type=f ."
```

[neovim]: https://neovim.io
[vundle]: https://github.com/VundleVim/Vundle.vim
[fzy]: https://github.com/jhawthorn/fzy
[fd]: https://github.com/sharkdp/fd
