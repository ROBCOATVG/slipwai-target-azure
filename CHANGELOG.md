# Changelog

No releases yet. Release notes are recorded here newest first, one entry per released version; the entry being
written is `changelog.d/`.

## 1.2.0 — MINOR

**The subscription keeps the passphrase that decrypts the committed bootstrap state.** The first
`make bootstrap` still generates one and prints it once, and the apply now keeps it as the secret
`state-passphrase` in a Key Vault of its own in the bootstrap group, RBAC like the service stack's, with the
applying sign-in as its secrets officer. The vault's name is written to `infra/passphrase-vault` beside the
state, and a later `make bootstrap` — from somebody else's laptop, say — signed in to the subscription reads
the secret back; `TF_VAR_state_passphrase` still overrides it. Whoever holds a secrets role on that vault may
decrypt the state, which is the trust the encrypted state already assumed.

**Catch-up:** `make bootstrap` once, with `TF_VAR_state_passphrase` set as before: that apply creates the
vault and the secret and writes `infra/passphrase-vault` — commit it with the state — and the next run needs
nothing.

## 1.1.0 — MINOR

**`./init` installs what bootstrapping Azure needs, through this package's own setup script.** The
package ships `scripts/setup.py` and names it as its `setup` hook, so `./init` runs it first: each tool —
OpenTofu and the Azure CLI — is installed with whatever the machine installs things with (`brew`, `winget`, or the tool's own installer),
and a machine with none of those is told the tool's own page, as before. A location is settled the same way: asked for at a terminal with `uksouth` on offer, taken as that without one, and written to `infra/location`, which is where `scripts/bootstrap.py` looks.
The CLI's sign-in is checked too (`az account show`), with `az login` run at a terminal where it fails.
`./init --no-install` only looks; `python3 scripts/setup.py --check` says what would be done.

**Catch-up:** `slipwai migrate` carries `scripts/setup.py` in and rewrites `./init`.

## 1.0.0

**Azure ships as a target package: `slipwai target install azure`, and `--target azure` is offered.** Everything
a project going to Azure is given is here rather than in the keel — the account stack and the service stack, the
scripts that bootstrap and deploy, the deployment drawing and the production decision record, the tools `./init`
checks for, the parts of the pipeline that are Azure's, and the answers that exist only here.

The keel it is built against names no cloud. That is the whole point of the move: a second place to deploy to is a
package somebody publishes, not a branch somebody adds to `generate`.

**Catch-up:** a project already generated with `--target azure` is unchanged. A keel upgraded past the move needs
`slipwai target install azure` before it will generate another one.

