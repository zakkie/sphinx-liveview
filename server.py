#!/usr/bin/env python
# coding=utf-8
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

import os.path
import logging
import weakref
import xml.parsers.expat

import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import options
import tornado.autoreload
import tornado.process

import watcher

websockets = weakref.WeakSet()
reload_script = """
<script src="/assets/alertify/lib/alertify.min.js"></script>
<link rel="stylesheet" href="/assets/alertify/themes/alertify.core.css" />
<link rel="stylesheet" href="/assets/alertify/themes/alertify.default.css" />
<script>
window.onload = function () {
  alertify.success( "loaded1" );
};

var ws = new WebSocket("ws://localhost:8888/ws");
ws.onmessage = function(e) {
  if (e.data == "reload") {
    location.reload(true);
  }
};
</script>
"""


class TagFound(Exception):
    pass


class MainHandler(tornado.web.RequestHandler):
    def get(self, path):
        """GET の実装。

        head 内に reload のための script を挿入する。/assets/ 以下は別の handler で処理するので
        script は挿入されない。
        """
        # need chroot?
        #logging.debug(self.absolute_path)
        #tornado.web.validate_absolute_path(path)
        if not os.path.exists(path):
            self.write_error(404)
            return

        def _tag_end(name):
            if name == 'head':
                raise TagFound
        xmlparser = xml.parsers.expat.ParserCreate()
        xmlparser.EndElementHandler = _tag_end
        try:
            with open(path) as f:
                xmlparser.ParseFile(f)
        except TagFound:
            pass
        else:
            self.write_error(500)
            return

        with open(path) as f:
            self.write(f.read(xmlparser.CurrentByteIndex - len("</head>")))
            self.write(reload_script)
            self.write("\n")
            self.write(f.read())


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        websockets.add(self)
        logging.debug('opened (%d)' % len(websockets))

    def on_close(self):
        try:
            websockets.remove(self)
        except KeyError:
            logging.warning("XXX")
        logging.debug('closed (%d)' % len(websockets))


def _reload(return_code):
    logging.debug('sending reload message')
    for ws in websockets:
        ws.write_message('reload')


def _run_cmd():
    if options.command:
        logging.debug('starting %s' % options.command)
        p = tornado.process.Subprocess(options.command, shell=True)
        p.set_exit_callback(_reload)
    else:
        _reload(0)


def main():
    options.define("port", default="8888")
    options.define("watch", type=str, multiple=True, default=".",
                   help="watch file or directory")
    options.define("htdoc", type=str, default=".", help="root directory of HTML documents")
    options.define("command", type=str, multiple=True, metavar="COMMAND",
                   help="run COMMAND when file or directory is changed")
    options.parse_command_line()

    mypath = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.join(mypath, 'assets')

    for f in options.watch:
        watcher.watch(f)

    watcher.add_hook(_run_cmd)
    watcher.start()

    application = tornado.web.Application([
        (r"/ws", WebSocketHandler),
        (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": assets_path}),
        (r"/(.*\.html)", MainHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": options.htdoc}),
    ])
    application.listen(8888)

    logging.info('starting application')
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info('bye')

main()
