import argparse
import logging

from moxie import create_app
from werkzeug.contrib import profiler

parser = argparse.ArgumentParser(description='Run the Flask application.')
parser.add_argument('--profiler', dest='profiler', help='Run the Flask app with a profiler.', action='store_true')
parser.add_argument('--no-default-settings', dest='use_default_settings', help="Don't use moxie's default settings.", action='store_false')
parser.add_argument('--log-level', dest='log_level', help='Specify the logging level.', default='INFO')
parser.add_argument('--host', dest='host', help='Hostname to run the dev server on.', default='127.0.0.1')
parser.add_argument('--port', type=int, dest='port', help='Port which the dev server should listen on.', default=5000)

args = parser.parse_args()

# %(module)s	%(funcName)s
FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'

logging.basicConfig(level=logging.getLevelName(args.log_level), format=FORMAT)

if args.profiler:
    action_profile = profiler.make_action(create_app)
    action_profile('localhost', 5000)
else:
    app = create_app(use_default_settings=args.use_default_settings)
    app.run(args.host, args.port)
