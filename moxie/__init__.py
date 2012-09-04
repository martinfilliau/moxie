from flask import Flask
from moxie.places import places


app = Flask(__name__, static_folder='core/static', template_folder='core/templates')
app.register_blueprint(places, url_prefix='/places')
