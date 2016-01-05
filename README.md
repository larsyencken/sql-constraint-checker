# sql-constraint-checker

Status: _experimental_

Run periodic SQL queries to perform basic sanity checks and ensure data quality. Where constraints are violated, get an example for you to begin debugging with.

## Overview

You configure the sanity checker with access to your database, preferably a read replica that's not used in production.

You then define in YAML a set of queries which are sanity checks, for example:

```yaml
name: gender-not-null
description: Users should have non-null gender
query_check: |
    SELECT COUNT(*)
    FROM user
    WHERE gender IS NULL
query_example: |
    SELECT *
    FROM user
    WHERE gender IS NULL
    LIMIT 1
warn_above: 0
alert_above: 100
```

This check would periodically run both the first and second queries. In the web UI, and in the API, it would display a warning if the number of users with this problem was greater than the 0, and an error if the number was above 100. The second query provides an example record which violates the constraint.

## Running

### Dependencies

You must have Python 3.4 or 3.5 installed, for example with `pyenv`. Then run:

```bash
make env
```

To install any depenencies.

### Configuring

You need to provide two files, `db.yml` and `checks.yml`.

For example, your `db.yml` should look like:

```yaml
host: some.db.domain.com
db: mydb
user: lars
passwd: likeskanelbullar
```

Your `checks.yml` looks like the example case above, with a triple dash `---` between each check.

### Polling

To run checks as a once-off, run:

```bash
make poll
```

This will regenerate a file `output.json` with the results of the checks.

### Serving

To run a debug server, run:

```bash
make serve
```

This will serve the current set of checks and any results to http://127.0.0.1:5000/.
