#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  poll.py
#  sql-sanity-checker
#

import pathlib
import json
import time
from collections import namedtuple
import datetime as dt
import decimal
import uuid

import click
import jsonschema
import yaml
import MySQLdb
import MySQLdb.cursors
import structlog

CHECK_SCHEMA = pathlib.Path(__file__).parent / 'schemas' / 'check.json'

structlog.configure(
    processors=[structlog.processors.JSONRenderer(sort_keys=True)]
)
LOG = structlog.get_logger()


@click.command()
@click.argument('config_file')
@click.argument('checks_file')
@click.argument('output_file')
@click.option('--last', is_flag=True,
              help='Only run the very last check in the file. Useful for development.')
def poll(config_file, checks_file, output_file, last=False):
    """
    Regenerate the output file by running the given checks against the
    database specified in our config.
    """
    checks = load_checks(checks_file)

    if last and checks:
        # only look at the last check
        checks = [checks[-1]]

    conn = connect_to_db(config_file)
    results = run_checks(checks, conn)
    dump_results(results, output_file)


def connect_to_db(config_file):
    with open(config_file) as istream:
        config = yaml.safe_load(istream)

    return MySQLdb.connect(cursorclass=MySQLdb.cursors.DictCursor,
                           **config)


def load_checks(checks_file):
    with open(CHECK_SCHEMA.as_posix()) as istream:
        schema = json.load(istream)

    checks = []
    with open(checks_file) as istream:
        for check in yaml.safe_load_all(istream):
            jsonschema.validate(check, schema)
            checks.append(check)

    return checks


def dump_results(results, output_file):
    output = json.dumps(results)
    with open(output_file, 'w') as ostream:
        print(output, file=ostream)


def run_checks(checks, conn):
    batch = LOG.bind(batch_id=str(uuid.uuid1()),
                     batch_timestamp=dt.datetime.now().isoformat())
    results = []

    with conn.cursor() as cursor:
        for check in checks:
            batch.msg(event='run-check', name=check['name'])
            check_result = run_check(check, cursor)
            result = assemble_result(check, check_result)
            results.append(result)

    return results


CheckResult = namedtuple('CheckResult', 'count example time')


def run_check(check, cursor):
    t = time.time()

    cursor.execute(check['query_check'])
    count, = cursor.fetchone().values()

    example = get_example(check, cursor)

    time_taken = time.time() - t

    return CheckResult(count, example, time_taken)


def get_example(check, cursor):
    query = check.get('query_example')
    if query:
        cursor.execute(query)
        return cursor.fetchone()


def assemble_result(check, check_result):
    return {
        'name': check['name'],
        'count': check_result.count,
        'time': check_result.time,
        'example': json_sanitize(check_result.example),
    }


def json_sanitize(o):
    "Turn the object into something we can jsonify."
    if isinstance(o, dict):
        return {k: json_sanitize(v) for k, v in o.items()}

    elif isinstance(o, list):
        return [json_sanitize(v) for v in o]

    elif isinstance(o, dt.date):
        return str(o)

    elif isinstance(o, decimal.Decimal):
        return float(o)

    return o


if __name__ == '__main__':
    poll()
