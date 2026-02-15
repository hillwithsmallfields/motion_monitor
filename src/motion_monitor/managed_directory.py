"""Manage the contents of a directory to keep the size under a limit."""

import datetime
import os
import subprocess
import time

import prefixed

def file_details(filename):
    """Return some details of a file as a dictionary."""
    stat = os.stat(filename)
    return {'filename': filename,
            'size': stat.st_size,
            'created': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()}

def full_filenames(directory, matching=None):
    """Return the full names of all the regular files in a directory.
    A matching function can be given, taking the filename as its only argument."""
    return [s for s in (os.path.join(directory, r)
                        for r in os.listdir(directory))
            if (os.path.isfile(s)
                and (matching is None
                     or matching(s)))]

def get_files_details(directory, matching=None):
    """Return the details of all the regular files in a directory.
    A matching function can be given, taking the filename as its only argument."""
    return [file_details(s) for s in full_filenames(directory, matching=matching)]

def recent_files_in_directory(directory, within_seconds=24*60*60, matching=None):
    """Return a list of the files in a directory that were modified within a given period.
    The period is given in seconds.  The default period is one day.
    A matching function can be given, taking the filename as its only argument."""
    cutoff = time.time() - within_seconds
    filenames = full_filenames(directory, matching=matching)
    print("recent_files_in_directory got", len(filenames), "before trimming by time")
    trimmed = [file_details(name)
               for name in filenames
               if os.stat(name).st_mtime > cutoff]
    print("recent_files_in_directory got", len(trimmed), "after trimming by time")
    return trimmed

def keep_days_in_directory(directory, keep_days=7):
    """Keep only a given number of days back in a clips directory."""
    cutoff = time.time() - keep_days*24*60*60
    deleted = 0
    kept = 0
    failed = 0
    for name in full_filenames(directory):
        if os.stat(name).st_mtime < cutoff:
            try:
                os.remove(name)
                deleted += 1
            except Exception as e:
                failed += 1
        else:
            kept += 1
    return {'deleted': deleted,
            'failed_to_delete': failed,
            'kept': kept}

def directory_size(directory):
    """Return the size of a directory, as reported by `du`."""
    return (prefixed.Float(subprocess.run(["du", "-s", directory],
                                          capture_output=True,
                                          encoding='utf8')
                           .stdout
                           .split('\t')
                           [0]))

def trim_directory(directory, trim_to="4Gb"):
    """Trim a clips directory to a given size."""
    limit = prefixed.Float(trim_to.removesuffix("b"))
    filenames = sorted(full_filenames(directory),
                       key=lambda filename: os.stat(filename).st_ctime,
                       reverse=True)
    while (filenames and (directory_size(directory) > limit)):
        try:
            filename = filenames.pop()
            os.remove(filename)
        except:
            print("Could not delete", filename, "while trimming directory", directory, "to", trim_to)
