from flask import Flask
from moxie.places.views import places


app = Flask(__name__)
app.register_blueprint(places)
