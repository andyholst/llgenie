# ci-verdict — the verdict never counts its own posted check-run

## ADDED Requirements

### Requirement: The verdict never counts its own posted check-run

The judge POSTs its verdict as a `ci-verdict` check-run on the judged run's head; GitHub lists that posted row
back as a job of the very run being judged. The verdict MUST exclude its own posted row from the job set it
judges, so a green run never reddens by reading its own echo.

WHEN  the judge holds a finished run to its scope decision
THEN  the verdict's own `ci-verdict` row is excluded from the judged job set
AND   the judge's own echo is never counted nor reported as a job failure.

#### Scenario: a green run whose own posted row says failure is green

Given a finished CI run whose every real job reported `success`,
And   GitHub lists the verdict's own posted `ci-verdict` check-run back as an 11th job with conclusion `failure`,
When  the judge holds the run to its scope decision,
Then  the `ci-verdict` row is excluded from the judged job set,
And   the verdict is `green` with the ten real jobs counted as success,
And   the `failure` on the judge's own echo is neither counted nor reported.

#### Scenario: a real unclassified failing job is still a red

Given a finished CI run whose real jobs are `success`,
And   a job the scope table does not name reports `failure` for its own reason,
When  the judge holds the run to its scope decision,
Then  that unknown job's failure is still counted as an unaccounted failure,
And   the verdict is `red` — removing the `ci-verdict` echo never hides a genuine failure.
