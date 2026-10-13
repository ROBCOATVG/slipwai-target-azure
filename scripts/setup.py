#!/usr/bin/env python3
"""What this target needs on the machine, put there by the target: `./init` runs this first.

Azure is bootstrapped and deployed with OpenTofu and the Azure CLI. `./init` used to look for them and name what was
missing; now it runs this, which installs each one with whatever this machine installs things with —
`brew`, `winget`, or the tool's own installer — or, with none of those, says where the tool's own page is, as before. A location is settled the same way: asked for at a terminal with `uksouth` on offer, taken as
that without one, and written to `infra/location`, which is where `scripts/bootstrap.py` looks. And the CLI's
sign-in is checked — `az account show` — with `az login` run at a terminal where it fails.

    python3 scripts/setup.py            # install what is missing, settle what is unset, sign in
    python3 scripts/setup.py --check    # say what would be done, and do nothing

Nothing here is the keel's: the keel runs this script and reads nothing from it, which is what keeps a
region, a package manager or a default a fact about Azure rather than a word the keel has to know.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Each tool, and the line that installs it per package manager, in the order they are tried. `sh` needs no
#: manager — it is the tool's own installer — so it comes last and always applies.
INSTALLS: dict[str, dict[str, str]] = {'az': {'brew': 'brew install azure-cli',
        'sh': 'curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash',
        'winget': 'winget install --id Microsoft.AzureCLI -e'},
 'tofu': {'brew': 'brew install opentofu',
          'sh': 'curl -fsSL https://get.opentofu.org/install-opentofu.sh -o '
                '/tmp/install-opentofu.sh && sh /tmp/install-opentofu.sh --install-method '
                'standalone && rm -f /tmp/install-opentofu.sh',
          'winget': 'winget install --id OpenTofu.Tofu -e'}}
#: Where each tool's own page is, for a machine with nothing that installs it.
WHERE = {'az': 'https://learn.microsoft.com/cli/azure/install-azure-cli',
 'tofu': 'https://opentofu.org/docs/intro/install/'}
#: What each manager is looked for as on the PATH; `sh` is always there.
PROBES = {"brew": "brew", "apt": "apt-get", "dnf": "dnf", "winget": "winget", "sh": "sh"}
#: Where a project lives when nobody said. Offered at the prompt and taken without a terminal — a location
#: has to be settled for `make bootstrap`; `infra/location` is where it is remembered, which is the file
#: `scripts/bootstrap.py` reads first.
DEFAULT_LOCATION = "uksouth"
LOCATION_FILE = ROOT / "infra/location"


def configured_location() -> str | None:
    if shutil.which("az") is None:
        return None
    done = subprocess.run(["az", "config", "get", "defaults.location", "--only-show-errors"],
                          text=True, capture_output=True)
    if done.returncode != 0:
        return None
    for line in done.stdout.splitlines():
        if '"value"' in line:
            return line.split(":", 1)[1].strip().strip(',').strip('"') or None
    return None


def settle_region(check: bool) -> None:
    """The location, if nothing says it yet: asked with the default on offer, or taken as the default, and
    written where `make bootstrap` reads it."""
    found = os.environ.get("AZURE_LOCATION") or configured_location()
    if not found and LOCATION_FILE.is_file():
        found = LOCATION_FILE.read_text(encoding="utf-8").strip() or None
    if found:
        say(f"Location: {found}.")
        return
    if check:
        say(f"would settle the location: ask, offering {DEFAULT_LOCATION}, and write infra/location")
        return
    chosen = ""
    if sys.stdin.isatty():
        chosen = input(f"Azure location for this project [{DEFAULT_LOCATION}]: ").strip()
    location = chosen or DEFAULT_LOCATION
    LOCATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCATION_FILE.write_text(location + "\n", encoding="utf-8")
    say(f"Location: {location}{' (the default; edit infra/location to change it)' if not chosen else ''} — wrote "
        f"infra/location; commit it with the bootstrap state.")


def signed_in() -> str | None:
    """The subscription the `az` CLI is signed in to, or None."""
    if shutil.which("az") is None:
        return None
    done = subprocess.run(["az", "account", "show", "--query", "name", "--output", "tsv", "--only-show-errors"],
                          text=True, capture_output=True)
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else None


def settle_sign_in(check: bool) -> bool:
    """Whether the CLI can reach a subscription. Not signed in and at a terminal, `az login` is run and asked
    again; `az account set --subscription <id>` is named for a person with more than one."""
    if shutil.which("az") is None:
        return False
    subscription = signed_in()
    if subscription:
        say(f"Signed in to Azure subscription {subscription}.")
        return True
    if check:
        say("would sign in: `az login`, then `az account set --subscription <id>` with more than one")
        return False
    if not sys.stdin.isatty():
        say("Not signed in to Azure: run `az login` (and `az account set --subscription <id>`), then `make bootstrap`.")
        return False
    say("Not signed in to Azure; running `az login`.")
    subprocess.run(["az", "login", "--only-show-errors"])
    subscription = signed_in()
    say(f"Signed in to Azure subscription {subscription}." if subscription else
        "Still not signed in; `make bootstrap` will say so again when it is run.")
    return bool(subscription)


def say(line: str) -> None:
    print(line, flush=True)


def install(tool: str, check: bool) -> bool:
    """Put one tool here with the first manager this machine has, or say where it comes from. Whether it is
    there afterwards."""
    for manager, line in INSTALLS[tool].items():
        if shutil.which(PROBES[manager]) is None:
            continue
        say(f"{'would install' if check else 'Installing'} {tool}: {line}")
        if check:
            return False
        done = subprocess.run(line, shell=True)
        if done.returncode != 0:
            say(f"{tool}: that did not finish (exit {done.returncode}); see {WHERE[tool]}")
        return shutil.which(tool) is not None
    say(f"{tool}: nothing on this machine installs it (tried {', '.join(INSTALLS[tool])}); see {WHERE[tool]}")
    return False


def main(argv: list[str]) -> int:
    check = "--check" in argv
    short = [tool for tool in INSTALLS if shutil.which(tool) is None]
    if not short:
        say("OpenTofu and the Azure CLI: all here.")
    left = [tool for tool in short if not install(tool, check)]
    settle_region(check)
    settle_sign_in(check)
    if left and not check:
        say(f"Still missing: {', '.join(left)}. `./init` carries on without the push and bootstrap.")
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
