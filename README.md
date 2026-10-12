# XMiniCore
This branch contains the Arduino IDE Boards Manager installation
support files. For more infomation see https://github.com/felias-fogg/XMiniCore.

There are two index files, and one installs either the one or the other, never
both: the board manager cannot have the same package offered by two indexes.

| File | For |
|---|---|
| `package_felias-fogg_XMiniCore_index.json` | the released versions, what the README of the core points at |
| `package_felias-fogg_XMiniCore_rc_index.json` | the same, plus the release candidates (tags `v*-rc*`) |

The release workflow picks the file by the tag and passes it to the scripts here
in `INDEX_FILE`. Run by hand without that variable, each of them writes the
released index, as they always did.
