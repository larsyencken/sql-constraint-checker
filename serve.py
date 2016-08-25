#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  serve.py
#  sql-sanity-checker
#

import os
import json
from collections import defaultdict

import click
import flask
import yaml
import jinja2_highlight  # noqa


@click.command()
@click.argument('checks_file')
@click.argument('results_file')
def serve(checks_file, results_file):
    app = ResultServer(checks_file, results_file)
    app.run(debug=True)


class ResultServer(flask.Flask):
    jinja_options = dict(flask.Flask.jinja_options)
    jinja_options.setdefault('extensions', []).append(
        'jinja2_highlight.HighlightExtension'
    )

    def __init__(self, checks_file, results_file):
        super().__init__('sql-sanity-checker')
        self.checks_file = checks_file
        self.results_file = results_file
        self.route('/')(self.serve_index)
        self.route('/<name>/')(self.serve_one)

    def serve_index(self):
        checks = self.load_results()
        ordered_checks = self.order_checks(checks)
        return flask.render_template('index.html', checks=ordered_checks)

    def serve_one(self, name):
        checks = self.load_results()
        if name not in checks:
            flask.abort(404)

        return flask.render_template('single.html', check=checks[name])

    def load_checks(self, checks_file):
        checks = {}
        with open(checks_file) as istream:
            for c in yaml.safe_load_all(istream):
                check = defaultdict(lambda: '-')
                check.update(c)

                checks[check['name']] = check

        return checks

    def load_results(self):
        checks = self.load_checks(self.checks_file)

        if os.path.exists(self.results_file):
            with open(self.results_file) as istream:
                results = json.load(istream)
        else:
            results = []

        for r in results:
            name = r['name']

            # ignore results for checks that aren't in our config
            if name in checks:
                checks[name].update(r)

        self.markup_checks(checks)

        return checks

    def order_checks(self, checks):
        results = list(checks.values())

        # reorder by status and name
        ordering = defaultdict(int)
        ordering['error'] = -3
        ordering['warning'] = -2
        ordering['ok'] = -1

        results.sort(key=lambda r: (ordering[r['status']], r['name']))

        return results

    def markup_checks(self, checks):
        for c in checks.values():
            print(c['name'])

            if 'time' in c:
                c['time_s'] = '{:.0f}'.format(c['time'])

            if 'warn_above' in c:
                c['warn_s'] = '>{}'.format(c['warn_above'])
            elif 'warn_below' in c:
                c['warn_s'] = '<{}'.format(c['warn_below'])

            if 'alert_above' in c:
                c['alert_s'] = '>{}'.format(c['alert_above'])
            elif 'alert_below' in c:
                c['alert_s'] = '<{}'.format(c['alert_below'])

            if 'count' in c:
                c['status'] = self.determine_status(c)

            if 'example' in c:
                c['example_s'] = json.dumps(c['example'],
                                            indent=2,
                                            sort_keys=True)

    def determine_status(self, check):
        count = check['count']
        if 'alert_above' in check and count > check['alert_above']:
            return 'error'
        elif 'alert_below' in check and count < check['alert_below']:
            return 'error'
        elif 'warn_above' in check and count > check['warn_above']:
            return 'warning'
        elif 'warn_below' in check and count < check['warn_below']:
            return 'warning'
        else:
            return 'ok'


if __name__ == '__main__':
    serve()
