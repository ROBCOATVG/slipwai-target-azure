"""Where the passphrase that decrypts the committed bootstrap state lives after the first run: in the
subscription.

The apply that writes it ends in somebody's subscription and is unprovable here. What is proved is the
script's side of it — a set passphrase wins, a first run makes one, a later run reads the subscription's copy
back with the `az` CLI from the vault the committed record names, and a project with no such record says what
to set rather than failing on an unreadable state — and that the stack declares the vault and the secret the
script reads, and waits for its own role assignment before writing.
"""
from __future__ import annotations

import importlib.util
import io
import contextlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PACKAGE = Path(__file__).resolve().parents[1]


def module(root: Path):
    spec = importlib.util.spec_from_file_location("bootstrap_passphrase_test", PACKAGE / "scripts/bootstrap.py")
    assert spec and spec.loader
    found = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(found)
    found.ROOT = root
    found.STACK = root / "infra/bootstrap"
    found.STATE = found.STACK / "terraform.tfstate"
    found.VAULT_FILE = root / "infra/passphrase-vault"
    found.STACK.mkdir(parents=True)
    return found


class PassphraseTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.script = module(Path(directory.name))

    def test_the_stack_keeps_it_in_a_vault_of_its_own_and_waits_for_its_own_grant(self) -> None:
        stack = (PACKAGE / "bootstrap/main.tf").read_text(encoding="utf-8")
        self.assertIn('resource "azurerm_key_vault" "bootstrap"', stack)
        self.assertIn("rbac_authorization_enabled = true", stack)
        self.assertIn('role_definition_name = "Key Vault Secrets Officer"', stack)
        self.assertIn('resource "azurerm_key_vault_secret" "state_passphrase"', stack)
        self.assertIn('name         = "state-passphrase"', stack)
        self.assertIn("depends_on = [time_sleep.passphrase_rbac]", stack)
        outputs = (PACKAGE / "bootstrap/outputs.tf").read_text(encoding="utf-8")
        self.assertIn('output "passphrase_vault"', outputs)
        self.assertEqual(self.script.RECORDED["infra/passphrase-vault"], "passphrase_vault",
                         "the vault's name is recorded beside the state, because reading it comes first")

    def test_a_set_passphrase_wins_and_nothing_is_asked_of_the_subscription(self) -> None:
        with mock.patch.dict("os.environ", {"TF_VAR_state_passphrase": "the-one-they-set"}), \
                mock.patch.object(self.script.subprocess, "run") as run:
            self.assertEqual(self.script.passphrase(), ("the-one-they-set", False))
        run.assert_not_called()

    def test_a_first_run_makes_one_long_enough_for_the_key_provider(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            phrase, fresh = self.script.passphrase()
        self.assertTrue(fresh)
        self.assertGreaterEqual(len(phrase), 16)

    def test_a_later_run_reads_the_subscription_s_copy_back_from_the_vault_the_record_names(self) -> None:
        self.script.STATE.write_text("{}", encoding="utf-8")
        self.script.VAULT_FILE.write_text("kvdemo1234abcd\n", encoding="utf-8")
        asked = []

        def az(command, **options):
            asked.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="kept-by-the-subscription\n", stderr="")

        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(self.script.subprocess, "run", az), \
                contextlib.redirect_stderr(io.StringIO()) as said:
            self.assertEqual(self.script.passphrase(), ("kept-by-the-subscription", False))
        self.assertEqual(asked[0][:4], ["az", "keyvault", "secret", "show"])
        self.assertEqual(asked[0][asked[0].index("--vault-name") + 1], "kvdemo1234abcd")
        self.assertEqual(asked[0][asked[0].index("--name") + 1], "state-passphrase")
        self.assertIn("read back from the subscription", said.getvalue())

    def test_a_project_with_no_record_says_what_to_set_instead_of_failing_on_the_state(self) -> None:
        """A project bootstrapped before the stack kept one has no `infra/passphrase-vault`; nothing is asked."""
        self.script.STATE.write_text("{}", encoding="utf-8")
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(self.script.subprocess, "run") as run, \
                self.assertRaises(self.script.Failure) as caught:
            self.script.passphrase()
        run.assert_not_called()
        self.assertIn("TF_VAR_state_passphrase", str(caught.exception))
        self.assertIn("passphrase-vault", str(caught.exception))

    def test_a_sign_in_that_may_not_read_the_vault_is_the_same_answer(self) -> None:
        self.script.STATE.write_text("{}", encoding="utf-8")
        self.script.VAULT_FILE.write_text("kvdemo1234abcd\n", encoding="utf-8")
        refused = subprocess.CompletedProcess([], 1, stdout="", stderr="Forbidden")
        with mock.patch.dict("os.environ", {}, clear=True), \
                mock.patch.object(self.script.subprocess, "run", lambda *a, **k: refused), \
                self.assertRaises(self.script.Failure):
            self.script.passphrase()


if __name__ == "__main__":
    unittest.main()
