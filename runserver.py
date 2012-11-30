import argparse
import logging

from moxie import create_app
from werkzeug.contrib import profiler

parser = argparse.ArgumentParser(description='Run the Flask application.')
parser.add_argument('--profiler', dest='profiler', help='Run the Flask app with a profiler.', action='store_true')
parser.add_argument('--log-level', dest='log_level', help='Specify the logging level.', default='INFO')

args = parser.parse_args()

logging.basicConfig(level=logging.getLevelName(args.log_level))

if args.profiler:
    action_profile = profiler.make_action(create_app)
    action_profile('localhost', 5000)
else:
    app = create_app()
    app.run()
