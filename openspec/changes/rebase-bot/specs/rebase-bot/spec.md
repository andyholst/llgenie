# rebase-bot

## ADDED Requirements

### Requirement: One PR per run, chosen from its merge state, with reasons

The sweep SHALL select at most one open, non-draft PR whose base is `main` and whose merge state is
`BEHIND` or `DIRTY`, oldest first, and SHALL report a reason for every PR it passes over. It SHALL
skip a PR that carries this bot's marker for the current UTC day and SHALL enforce a daily cap.

#### Scenario: the oldest PR that needs it is picked

- **GIVEN** a clean PR, a draft, a PR against another base, a conflicted PR and a behind PR
- **WHEN** the sweep runs
- **THEN** it SHALL select the conflicted one (oldest needing attention), and name the others

#### Scenario: nothing twice in a day

- **GIVEN** a PR whose marker comment carries today's date
- **WHEN** the sweep runs
- **THEN** it SHALL not select it again

### Requirement: A conflict is resolved by the agent, verified, and published to the PR's own remote

The actor SHALL rebase with `rerere` disabled. On a conflict it SHALL hand the stopped rebase to
the agent with the rule to preserve both sides, and SHALL NOT publish while conflict markers
remain. Before pushing it SHALL run the structural checks. It SHALL push with
`--force-with-lease` to the repository that hosts the PR's head branch, and SHALL NOT merge.

#### Scenario: a conflicting PR comes back onto main

- **GIVEN** a branch conflicting with `main`, and an agent that resolves it
- **THEN** the rebase SHALL complete, both sides' content SHALL survive
- **AND** the branch SHALL be pushed to the PR's head remote with the lease

#### Scenario: a plain force is never used

- **WHEN** the push command is inspected
- **THEN** it SHALL carry `--force-with-lease` and never a bare `--force`

#### Scenario: a failed resolution publishes nothing

- **GIVEN** an agent that fails
- **WHEN** the actor runs
- **THEN** it SHALL exit non-zero and the head branch SHALL be unchanged
