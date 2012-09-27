import argparse

from moxie import create_app
from werkzeug.contrib import profiler

parser = argparse.ArgumentParser(description='Run the Flask application.')
parser.add_argument('--profiler', dest='profiler', help='Run the Flask app with a profiler.', action='store_true')

args = parser.parse_args()

if args.profiler:
    action_profile = profiler.make_action(create_app)
    action_profile('localhost', 5000)
else:
    app = create_app()
    app.run()