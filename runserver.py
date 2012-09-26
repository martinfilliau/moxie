from moxie import create_app
from werkzeug.contrib import profiler
action_profile = profiler.make_action(create_app)
action_profile('localhost', 5000)
