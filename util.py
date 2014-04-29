#!/usr/bin/env python

import os
import signal
import datetime
from termcolor import colored


def basename(path):
    if path.endswith("/"):
        tmp = path[:-1]
    else:
        tmp = path
    return os.path.basename(tmp)


def isdir(up, path):
    try:
        ret = up.getinfo(path)
        if ret['file-type'] == 'folder':
            return True
        return False
    except:
        return False


def exists(up, path):
    try:
        ret = up.getinfo(path)
    except:
        return False
    return True


def walk(up, path):
    ret = up.getlist(path)
    files = []
    dirs = []
    for ff in ret:
        if ff['type'] == 'N':
            files.append(ff['name'])
        elif ff['type'] == 'F':
            dirs.append(ff['name'])
    return path, dirs, files


def pretty_print(lines):
    for line in lines:
        if line['type'] == "F":
            name = colored(line['name'], "blue")
        else:
            name = line['name']

        size = line['size']
        tmp = datetime.datetime.fromtimestamp(int(line['time']))
        time = tmp.strftime('%Y-%m-%d %H:%M:%S')
        print time, size.ljust(7), name
