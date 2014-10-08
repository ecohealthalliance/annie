#!/usr/bin/env python
"""Profiling"""

import datetime
import cProfile
import pstats
from collections import defaultdict
import functools

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.profiling
profile_coll = db.profile
cprofile_coll = db.cprofile

def insert_profile(time, key, namespace):
    profile_coll.update(
        { 'namespace': namespace, 'key': key },
        { '$inc': { 'calls': 1,
                    'cumulative_time': time },
          '$push': { 'times': time } },
        upsert=True)

def insert_cprofile(profile, namespace):
    profile_stats = pstats.Stats(profile).stats.items()

    for item in profile_stats:
        key = make_cprofile_key(item)
        primitive_calls = item[1][0]
        all_calls = item[1][1]
        total_time = item[1][2]
        cumulative_time = item[1][3]
        cprofile_coll.update(
            { 'namespace': namespace, 'key': key },
            { '$inc': { 'primitive_calls': primitive_calls,
                        'all_calls': all_calls,
                        'total_time': total_time,
                        'cumulative_time': cumulative_time }
            },
            upsert=True)

def clear_profile():
    profile_coll.drop()

def clear_cprofile():
    cprofile_coll.drop()

def clear_all():
    clear_profile()
    clear_cprofile()

def get_milliseconds_from_timedelta(delta):
    return ( (delta.days * 24 * 60 * 1000) +
             (delta.seconds * 1000) +
             (delta.microseconds * 0.001) )

class Profiled(object):

    def __init__(self, namespace):
        self.namespace = namespace

    def __call__(self, fn):
        @functools.wraps(fn)
        def _profiled(*args, **kwargs):
            key = fn.__module__ + '.' + fn.__name__
            start = start = datetime.datetime.now()
            result = fn(*args, **kwargs)
            elapsed = datetime.datetime.now() - start
            elapsed_milliseconds = get_milliseconds_from_timedelta(elapsed)

            insert_profile(elapsed_milliseconds, key, self.namespace)

            return result

        return _profiled

class CProfiled(object):

    def __init__(self, namespace):
        self.namespace = namespace
        self.profile = cProfile.Profile()

    def __call__(self, fn):
        @functools.wraps(fn)
        def _profiled(*args, **kwargs):
            self.profile.clear()
            self.profile.enable()
            result = fn(*args, **kwargs)
            self.profile.disable()

            insert_cprofile(self.profile, self.namespace)

            return result

        return _profiled

def get_stats():
    return pstats.Stats(profile).stats

def seconds_to_ms(sometime):
    """turn seconds into milliseconds"""
    return sometime * 1000

def format_time(sometime):
    """round to two decimal places"""
    return round(sometime, 2)

def make_cprofile_key(item):
    return ':'.join([ str(val) for val in item[0]])

def get_cprofile_table(namespace=None, sort_by='cumulative_time'):
    """Return HTML to produce a sorted table of cprofile profiling statistics"""

    header = """<table id="stats">
                    <tr>
                        <th>namespace</th>
                        <th>call</th>
                        <th>primitive calls</th>
                        <th>all calls</th>
                        <th>total time</th>
                        <th>tt per call</th>
                        <th>cumulative time</th>
                        <th>ct per call</th>
                    </tr>
                """
    footer = '</table>'
    rows = []

    criteria = {}
    if namespace:
        criteria['namespace'] = namespace

    for item in cprofile_coll.find(criteria):
        row = {}
        row['namespace'] = item['namespace']
        row['function'] = item['key']
        row['primitive_calls'] = item['primitive_calls']
        row['all_calls'] = item['all_calls']
        row['total_time'] = format_time(seconds_to_ms(item['total_time']))
        row['tt_per_call'] = format_time(row['total_time'] / row['all_calls'])
        row['cumulative_time'] = format_time(seconds_to_ms(item['cumulative_time']))
        row['ct_per_call'] = format_time(row['cumulative_time'] / row['primitive_calls'])
        rows.append(row)

    if sort_by == 'function':
        rows.sort(key=lambda x: x[sort_by])
    else:
        rows.sort(key=lambda x: -x[sort_by])

    html_rows = []

    keys = ['namespace', 'function', 'primitive_calls', 'all_calls', 'total_time', 'tt_per_call',
            'cumulative_time', 'ct_per_call']
    for row in rows:
        html_rows.append('<tr>' + '\n'.join( [ '<td>' + str(row[key]) + '</td>' for key in keys ] ) + '</tr>')

    return header + '\n'.join(html_rows) + footer

def get_profile_table(namespace=None, sort_by='cumulative_time'):
    """Return HTML to produce a sorted table of our own profiling statistics"""

    header = """<table id="stats">
                    <tr>
                        <th>namespace</th>
                        <th>call</th>
                        <th># calls</th>
                        <th>cumulative time</th>
                        <th>ct per call</th>
                    </tr>
                """
    footer = '</table>'
    rows = []

    criteria = {}
    if namespace:
        criteria['namespace'] = namespace

    for item in profile_coll.find(criteria):
        row = {}
        row['namespace'] = item['namespace']
        row['function'] = item['key']
        row['calls'] = item['calls']
        row['cumulative_time'] = format_time(item['cumulative_time'])
        row['ct_per_call'] = format_time(row['cumulative_time'] / row['calls'])
        rows.append(row)

    if sort_by == 'function':
        rows.sort(key=lambda x: x[sort_by])
    else:
        rows.sort(key=lambda x: -x[sort_by])

    html_rows = []

    keys = ['namespace', 'function', 'calls', 'cumulative_time', 'ct_per_call']
    for row in rows:
        html_rows.append('<tr>' + '\n'.join( [ '<td>' + str(row[key]) + '</td>' for key in keys ] ) + '</tr>')

    return header + '\n'.join(html_rows) + footer
