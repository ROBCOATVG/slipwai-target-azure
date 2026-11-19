# Changelog

No releases yet. Release notes are recorded here newest first, one entry per released version; the entry being
written is `changelog.d/`.

## 1.3.1 — PATCH

**CI proves this package against slipwai itself.** Its workflow installed the keel, called the shared release workflow and took the cloud target sources from `ROBCOATVG/slipwai_v2_Fork`, a fork archived on 2026-10-17 and 244 commits behind `ROBCOATVG/slipwai`. All of them now come from `ROBCOATVG/slipwai`; where a commit is pinned, it is the same commit, which both repositories hold. Nothing the package does in a project changes.

**CI's keel moves from 2026-10-12 (`18505e8d`) to slipwai's current `main` (`7beb78a7`).** The `stacks` job generates a real project with the published TypeScript language, which needs a newer keel than the one pinned here, so the job had failed on `main` since 2026-11-18. Against today's keel a pruned region's file is removed rather than left empty, and the stack tests now hold it to that.

## 1.3.0 — MINOR

**A project pushed before its subscription is ready keeps a green trunk.** `deploy.yml` started on every push
to `main` that passed `verify`, and failed at `azure/login` with `Not all values are present` until `make
bootstrap` had written the repository's variables — and a fleet's harbourmaster lands nothing while trunk is
red. The pipeline now answers the keel's optional `configured` key with `AZURE_CLIENT_ID`, the variable every
sign-in reads; a keel that reads it skips the deploy, `production.yml` and `rollback.yml` whole until the
variable is set, and the first push after `make bootstrap` deploys. A keel older than the key ignores it and
generates the workflows it always did.

**Catch-up:** run `slipwai migrate` in a project generated for Azure and commit the workflow files it
rewrites.

**A project generated for Azure no longer begins with a red trunk.** The deploy and rollback workflows chose
between the federated sign-in and the client secret with `if: ${{ secrets.AZURE_CLIENT_SECRET == '' }}` on a
step. GitHub does not offer `secrets` in an `if:`, and refuses the whole workflow file before any job is
made, with no log — so `deploy.yml`, `rollback.yml` and a liner's `production.yml` failed on every push from
the first commit, and a fleet's trunk mender, which may not edit an `if:`, could not clear it. Each job now
asks once, in a step of its own, whether the secret is set, and the two sign-ins are chosen from that step's
output.

**Catch-up:** run `slipwai migrate` in a project generated for Azure and commit the three workflow files it
rewrites; trunk goes green on that push.

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

