#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import psutil
import re
import socket
import sys
import subprocess
import time

import managed_directory

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-files", "-l", action='store_true')
    parser.add_argument("--keep-days", "-k", type=int)
    parser.add_argument("--wipeout", "-w", action='store_true')
    parser.add_argument("--trim", "-t", default="2G")
    return vars(parser.parse_args())

def get_live_command_lines_matching(matching):
    """Get the command lines for current processes running a given program."""
    return [cmdline
            for cmdline in (proc.cmdline()
                            for proc in (psutil.Process(pid) for pid in psutil.pids())
                            if proc.status() != 'zombie')
            if cmdline and cmdline[0].endswith(matching)]

def get_option_value(cmdline, option):
    """Get the value for a selected command-line option."""
    pattern = "--%s=(.+)" % option
    for i, v in enumerate(cmdline):
        if v == option:
            return (cmdline[i+1] if i < len(cmdline) else None)
        if (m := re.match(pattern, v)):
            return m.group(1)
    return None

def get_motion_config_filename():
    """Get the filename in current use as a motion config."""
    motions = get_live_command_lines_matching("motion")
    if len(motions) > 1:
        raise RuntimeError("More than one motion process")
    if len(motions) == 0:
        raise RuntimeError("No motion process")
    return get_option_value(motions[0], "-c")

def get_config_value(filename, key):
    """Get a value from a motion config filename."""
    with open(filename) as instream:
        for line in instream:
            parts = line.split()
            if parts:
                if parts[0] == key:
                    return parts[1]
    return None

def get_clips_directory():
    """Get the clips directory in current use."""
    return get_config_value(get_motion_config_filename(), "target_dir")

def run_on_host(hostname, command):
    """Run a command on a specified host."""
    if socket.gethosthame() == hostname:
        return subprocess.run(command).stdout
    else:
        return subprocess.run(["ssh", hostname, command]).stdout

def motion_main(list_files, keep_days, wipeout, trim):
    clips_dir = get_clips_directory ()
    if list:
        json.dump(managed_directory.get_files_details(clips_dir),
                  sys.stdout)
    if wipeout:
        deleted = 0
        failed = 0
        for filename in managed_directory.full_filenames(clips_dir):
            try:
                os.remove(filename)
                deleted += 1
            except:
                failed += 1
        json.dump({'deleted': deleted,
                   'failed_to_delete': failed}, sys.stdout)
    if keep_days:
        json.dump(managed_directory.keep_days_in_directory(clips_dir, keep_days),
                  sys.stdout)
    if trim:
        managed_directory.trim_directory(clips_dir, trim)

if __name__ == "__main__":
    motion_main(**get_args())
