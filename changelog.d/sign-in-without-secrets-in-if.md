PATCH

**A project generated for Azure no longer begins with a red trunk.** The deploy and rollback workflows chose
between the federated sign-in and the client secret with `if: ${{ secrets.AZURE_CLIENT_SECRET == '' }}` on a
step. GitHub does not offer `secrets` in an `if:`, and refuses the whole workflow file before any job is
made, with no log — so `deploy.yml`, `rollback.yml` and a liner's `production.yml` failed on every push from
the first commit, and a fleet's trunk mender, which may not edit an `if:`, could not clear it. Each job now
asks once, in a step of its own, whether the secret is set, and the two sign-ins are chosen from that step's
output.

**Catch-up:** run `slipwai migrate` in a project generated for Azure and commit the three workflow files it
rewrites; trunk goes green on that push.
