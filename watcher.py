#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Copyright 2013 Akihiro YAMAZAKI <zakkie@outlook.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Call registered functions when watching files are modified.

Thins module inspired from tornado.autoreload
"""

import os
import traceback
import weakref

from tornado import ioloop
from tornado.log import gen_log

_watched_files = {}
_hook_funcs = []
_reload_attempted = False
_io_loops = weakref.WeakKeyDictionary()


def start(io_loop=None, check_time=500):
    io_loop = io_loop or ioloop.IOLoop.current()
    if io_loop in _io_loops:
        return
    _io_loops[io_loop] = True
    if len(_io_loops) > 1:
        gen_log.warning("watcher started more than once in the same process")
    scheduler = ioloop.PeriodicCallback(_check_files, check_time, io_loop=io_loop)
    scheduler.start()


def _add_watching(path):
    try:
        last_modified = os.stat(path).st_mtime
    except:
        gen_log.warning("failed to watch %s" % path)
        traceback.print_exc()
        return
    _watched_files[path] = last_modified


def watch(filepath):
    if os.path.isdir(filepath):
        for dirpath, _, files in os.walk(filepath):
            _add_watching(dirpath)
            map(lambda x:_add_watching(os.path.join(dirpath, x)), files)
    else:
        _add_watching(filepath)


def add_hook(fn):
    _hook_funcs.append(fn)


def _check_files():
    fire = False
    for path, last_modified in _watched_files.iteritems():
        try:
            modified = os.stat(path).st_mtime
        except Exception:
            traceback.print_exc()
            continue
        if last_modified != modified:
            fire = True
            _watched_files[path] = modified
    if fire:
        for func in _hook_funcs:
            func()


def main():
    def callback():
        print "callbacked"
    import sys
    filepath = sys.argv[1]
    watch(filepath)
    print _watched_files
    add_hook(callback)
    io_loop = ioloop.IOLoop()
    start(io_loop)
    io_loop.start()

if __name__ == "__main__":
    main()
