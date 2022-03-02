from flask import Flask
from blueprints.endpoints import blueprint as gilson_REST
from blueprints.endpoints.plotlydash.uvstdapp import init_dashboard
from waitress import serve


# Initializing the app
app = Flask(__name__)

app.register_blueprint(gilson_REST)
app = init_dashboard(app) # Registers Sharyua's app

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
    #serve(app, host='0.0.0.0', port=5000)