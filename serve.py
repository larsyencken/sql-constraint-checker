#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  serve.py
#  sql-sanity-checker
#

import json

import click
import flask
import yaml


@click.command()
@click.argument('checks_file')
@click.argument('results_file')
def serve(checks_file, results_file):
    app = ResultServer(checks_file, results_file)
    app.run(debug=True)


class ResultServer(flask.Flask):
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
        with open(checks_file) as istream:
            return {c['name']: c
                    for c in yaml.safe_load_all(istream)}

    def load_results(self):
        checks = self.load_checks(self.checks_file)

        with open(self.results_file) as istream:
            results = json.load(istream)

        for r in results:
            checks[r['name']].update(r)

        self.markup_checks(checks)

        return checks

    def order_checks(self, checks):
        results = list(checks.values())
        results.sort(key=lambda r: r['name'])
        results = ([r for r in results if r['status'] == 'error']
                   + [r for r in results if r['status'] == 'warning']
                   + [r for r in results if r['status'] == 'ok'])

        return results

    def markup_checks(self, checks):
        for c in checks.values():
            c['time_s'] = '{:.0f}'.format(c['time'])

            if 'warn_above' in c:
                c['warn_s'] = '>{}'.format(c['warn_above'])
            elif 'warn_below' in c:
                c['warn_s'] = '<{}'.format(c['warn_above'])
            else:
                c['warn_s'] = '-'

            if 'alert_above' in c:
                c['alert_s'] = '>{}'.format(c['alert_above'])
            elif 'alert_below' in c:
                c['alert_s'] = '<{}'.format(c['alert_above'])
            else:
                c['alert_s'] = '-'

            c['status'] = self.determine_status(c)
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
