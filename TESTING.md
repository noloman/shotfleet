# Testing

`tools/check-claims.sh` runs everything (unit tests, the site and claims guardrails, the worker tests) and prints one line. It takes about 15 seconds.
Turn it into a pre-commit check once per clone: `git config core.hooksPath .githooks`. `packaging/release.sh` runs it too. CI (`.github/workflows/ci.yml`) is manual-only (Actions tab, `workflow_dispatch`): the local run is the gate and no runner minutes are spent per push.

Every public promise is a row in `tests/claims.json` (status, proof, the exact words it quotes). Change a promise's words and `tests/test_claims.py` tells you which row to update.
`tests/test_site.py` guards the site (links, alt text, one price, banned phrases, the go-live transform, CSP); `tests/test_cli_claims.py` checks what the site and README say the program prints and accepts.
