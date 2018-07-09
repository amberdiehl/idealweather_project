from flask import Flask

import config
import commands
import models
from views import (Home, ExploreHumidity, HumidityDataAsList, ExploreStation, StationDataAsList, ExploreTemperature,
                   TemperatureDataAsList, AjaxGetStations, )


app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.cli.add_command(commands.import_data)
app.cli.add_command(commands.list_weather)


@app.before_request
def before_request():
    config.DATABASE.connect()


@app.after_request
def after_request(response):
    config.DATABASE.close()
    return response


app.add_url_rule('/', view_func=Home.as_view('home'))
app.add_url_rule('/humidity', view_func=ExploreHumidity.as_view('explore_humidity'))
app.add_url_rule('/humidity-datalist', view_func=HumidityDataAsList.as_view('humidity_datalist'))
app.add_url_rule('/station', view_func=ExploreStation.as_view('explore_station'))
app.add_url_rule('/station-datalist', view_func=StationDataAsList.as_view('station_datalist'))
app.add_url_rule('/temperature', view_func=ExploreTemperature.as_view('explore_temperature'))
app.add_url_rule('/temperature-datalist', view_func=TemperatureDataAsList.as_view('temperature_datalist'))
app.add_url_rule('/ajax/stations/<state>', view_func=AjaxGetStations.as_view('ajax_stations'))


if __name__ == '__main__':
    models.initialize()
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
