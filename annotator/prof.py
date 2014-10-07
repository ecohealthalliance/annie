#!/usr/bin/env python
"""Profiling"""

import datetime
import cProfile
import pstats
from collections import defaultdict

profile = cProfile.Profile()

class Timing:

    def __init__(self):

        self.calls = 0
        self.cumulative_time = 0 # in milliseconds
        self.times = []

    def add_time(self, time):
        self.calls += 1
        self.cumulative_time += time
        self.times.append(time)

timings = defaultdict(Timing)

def get_milliseconds_from_timedelta(delta):
    return ( (delta.days * 24 * 60 * 1000) +
             (delta.seconds * 1000) +
             (delta.microseconds * 0.001) )

def profiled(func):
    def profiled_func(*args, **kwargs):
        key = func.__module__ + '.' + func.__name__

        profile.enable()
        start = start = datetime.datetime.now()
        result = func(*args, **kwargs)
        elapsed = datetime.datetime.now() - start
        elapsed_milliseconds = get_milliseconds_from_timedelta(elapsed)
        profile.disable()

        timings[key].add_time(elapsed_milliseconds)

        return result

    return profiled_func

def get_stats():
    return pstats.Stats(profile).stats

def seconds_to_ms(sometime):
    """turn seconds into milliseconds"""
    return sometime * 1000

def format_time(sometime):
    """round to two decimal places"""
    return round(sometime, 2)

def get_cprofile_stats_table(sort_by='cumulative_time'):
    """Return HTML to produce a sorted table of cprofile profiling statistics"""

    profile_stats = pstats.Stats(profile).stats.items()

    header = """<table id="stats">
                    <tr>
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

    for item in profile_stats:
        row = {}
        row['function'] = ':'.join([ str(val) for val in item[0]])
        row['primitive_calls'] = item[1][0]
        row['all_calls'] = item[1][1]
        row['total_time'] = format_time(seconds_to_ms(item[1][2]))
        row['tt_per_call'] = format_time(row['total_time'] / row['all_calls'])
        row['cumulative_time'] = format_time(seconds_to_ms(item[1][3]))
        row['ct_per_call'] = format_time(row['cumulative_time'] / row['primitive_calls'])
        rows.append(row)

    if sort_by == 'function':
        rows.sort(key=lambda x: x[sort_by])
    else:
        rows.sort(key=lambda x: -x[sort_by])

    html_rows = []

    keys = ['function', 'primitive_calls', 'all_calls', 'total_time', 'tt_per_call',
            'cumulative_time', 'ct_per_call']
    for row in rows:
        html_rows.append('<tr>' + '\n'.join( [ '<td>' + str(row[key]) + '</td>' for key in keys ] ) + '</tr>')

    return header + '\n'.join(html_rows) + footer

def get_stats_table(sort_by='cumulative_time'):
    """Return HTML to produce a sorted table of our own profiling statistics"""

    header = """<table id="stats">
                    <tr>
                        <th>call</th>
                        <th># calls</th>
                        <th>cumulative time</th>
                        <th>ct per call</th>
                    </tr>
                """
    footer = '</table>'
    rows = []

    for item in timings.items():
        row = {}
        row['function'] = item[0]
        row['calls'] = item[1].calls
        row['cumulative_time'] = format_time(item[1].cumulative_time)
        row['ct_per_call'] = format_time(row['cumulative_time'] / row['calls'])
        rows.append(row)

    if sort_by == 'function':
        rows.sort(key=lambda x: x[sort_by])
    else:
        rows.sort(key=lambda x: -x[sort_by])

    html_rows = []

    keys = ['function', 'calls', 'cumulative_time', 'ct_per_call']
    for row in rows:
        html_rows.append('<tr>' + '\n'.join( [ '<td>' + str(row[key]) + '</td>' for key in keys ] ) + '</tr>')

    return header + '\n'.join(html_rows) + footer
