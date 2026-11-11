# Contributing to shotfleet

shotfleet is open source under the [MIT license](LICENSE). Bug reports, fixes and ideas are welcome.

- **Bugs and ideas:** open a [GitHub issue](https://github.com/noloman/shotfleet/issues). For a bug, the output of `shotfleet doctor` and the failing command help most.
- **Pull requests:** keep each one to a single change. Run `tools/check-claims.sh` before you push; it runs the unit tests, the website guardrails and the site worker tests (about a minute). Turn it into a pre-commit check once per clone with `git config core.hooksPath .githooks`.
- **Words are tested:** every promise the README and the site make is a row in `tests/claims.json`. If you change what the program does or says, the tests tell you which row to update.
- **Releases** are built and published by the maintainer from a Mac (`packaging/publish.sh`), not by CI.

If shotfleet saves you time, you can support its development through [GitHub Sponsors](https://github.com/sponsors/noloman).
