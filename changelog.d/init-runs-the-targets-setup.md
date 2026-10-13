MINOR

**`./init` installs what bootstrapping Azure needs, through this package's own setup script.** The
package ships `scripts/setup.py` and names it as its `setup` hook, so `./init` runs it first: each tool —
OpenTofu and the Azure CLI — is installed with whatever the machine installs things with (`brew`, `winget`, or the tool's own installer),
and a machine with none of those is told the tool's own page, as before. A location is settled the same way: asked for at a terminal with `uksouth` on offer, taken as that without one, and written to `infra/location`, which is where `scripts/bootstrap.py` looks.
The CLI's sign-in is checked too (`az account show`), with `az login` run at a terminal where it fails.
`./init --no-install` only looks; `python3 scripts/setup.py --check` says what would be done.

**Catch-up:** `slipwai migrate` carries `scripts/setup.py` in and rewrites `./init`.
