#!/usr/bin/env python

import argparse
import logging
import os
import sys
from threading import Thread
from time import sleep
import tornado.ioloop
import tornado.httpserver
import tornado.web

import hermes
from hermes import version
from hermes.app import Application
from hermes.settings import settings
from hermes.models import get_db_engine, Session


from sqlalchemy.exc import OperationalError

sa_log = logging.getLogger("sqlalchemy.engine.base.Engine")


def main(argv):

    parser = argparse.ArgumentParser(description="Event Management Service ")
    parser.add_argument("-c", "--config", default="/etc/nsot.yaml",
                        help="Path to config file.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity.")
    parser.add_argument("-q", "--quiet", action="count", default=0, help="Decrease logging verbosity.")
    parser.add_argument("-V", "--version", action="version",
                        version="%%(prog)s %s" % hermes.__version__,
                        help="Display version information.")
    parser.add_argument("-p", "--port", type=int, default=None, help="Override port in config.")
    args = parser.parse_args()
    settings.update_from_config(args.config)

    tornado_settings = {
        "static_path": os.path.join(os.path.dirname(hermes.__file__), "static"),
        "debug": settings.debug,
        "xsrf_cookies": True,
        "cookie_secret": settings.secret_key,
    }

    db_engine = get_db_engine(settings.database)
    Session.configure(bind=db_engine)

    my_settings = {
        "db_engine": db_engine,
        "db_session": Session,
    }

    application = Application(my_settings=my_settings, **tornado_settings)

    port = args.port or settings.port

    logging.info(
        "Starting application server with %d processes on port %d",
        settings.num_processes, port
    )

    server = tornado.httpserver.HTTPServer(application)
    server.bind(port, address=settings.bind_address)
    server.start()
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
    finally:
        print "Bye"


if __name__ == "__main__":
    main(sys.argv)
