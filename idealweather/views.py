from flask import render_template, flash, redirect, url_for, session, jsonify
from flask.views import MethodView
from forms import HumiditySelectionForm, StationSelectionForm, TemperatureSelectionForm
from models import Station
from helpers import (create_queryset_for_station_as_list, create_queryset_for_humidity_as_list,
                     create_queryset_for_temperature_as_list, format_dataset_for_list_views)


def get_previous_selections():
    weather = session.get('weather', None)
    if weather is None:
        session['weather'] = {'months': [],
                              'percentage': {},
                              'state': '',
                              'station': 'all',
                              'temperature_high': 0,
                              'temperature_low': 0}
        return session['weather']
    return weather


SEASON_MAP = ['wi', 'wi', 'sp', 'sp', 'sp', 'su', 'su', 'su', 'au', 'au', 'au', 'wi']


class Home(MethodView):

    def get(self):

        return render_template('home.html')


class ExploreHumidity(MethodView):

    def get(self):

        initialize = {}
        if 'weather' in session:
            if len(session['weather']['months']) > 0:
                if len(session['weather']['months']) == 1:
                    initialize['time_period'] = 'month'
                    initialize['month'] = session['weather']['months'][0]
                else:
                    initialize['time_period'] = 'season'
                    initialize['season'] = SEASON_MAP[int(session['weather']['months'][0][4:]) - 1]
                for key, value in session['weather']['percentage'].items():
                    initialize[key] = int(value * 100)

        form = HumiditySelectionForm(**initialize)
        return render_template('humidity_selection.html', form=form)


    def post(self):

        form = HumiditySelectionForm()
        if form.validate_on_submit():

            weather = get_previous_selections()
            if form.time_period.data == 'season':
                if form.season.data == 'wi':
                    weather['months'] = ['201701', '201702', '201712']
                if form.season.data == 'sp':
                    weather['months'] = ['201703', '201704', '201705']
                if form.season.data == 'su':
                    weather['months'] = ['201706', '201707', '201708']
                if form.season.data == 'au':
                    weather['months'] = ['201709', '201710', '201711']
            else:
                weather['months'] = ['2017' + form.month.data]

            weather['percentage']['le20'] = float(form.le20.data) / 100
            weather['percentage']['lt40'] = float(form.lt40.data) / 100
            weather['percentage']['target'] = float(form.target.data) / 100
            weather['percentage']['gt60'] = float(form.gt60.data) / 100
            weather['percentage']['ge80'] = float(form.ge80.data) / 100
            session['weather'] = weather

            return redirect(url_for('humidity_datalist'))
        else:
            return render_template('humidity_selection.html', form=form)


class HumidityDataAsList(MethodView):

    def get(self):

        weather = session['weather']
        qs = create_queryset_for_humidity_as_list(weather)
        stations = format_dataset_for_list_views(qs)

        return render_template('humidity_listdata.html', weather=weather, stations=stations)


class ExploreStation(MethodView):

    def get(self):

        initialize = {}
        if 'weather' in session:
            if session['weather']['state']:
                initialize['state'] = session['weather']['state']
                initialize['station'] = session['weather']['station']

        form = StationSelectionForm(**initialize)
        return render_template('station_selection.html', form=form)

    def post(self):

        form = StationSelectionForm()
        if form.validate_on_submit():

            weather = get_previous_selections()
            weather['state'] = form.state.data
            weather['station'] = form.station.data
            session['weather'] = weather

            return redirect(url_for('station_datalist'))
        else:
            return render_template('station_selection.html', form=form)


class StationDataAsList(MethodView):

    def get(self):

        weather = session['weather']
        qs = create_queryset_for_station_as_list(weather)
        stations = format_dataset_for_list_views(qs)

        return render_template('station_listdata.html', weather=weather, stations=stations)


class ExploreTemperature(MethodView):

    def get(self):

        initialize = {}
        if 'weather' in session:
            if session['weather']['temperature_high']:
                initialize['temperature_high'] = session['weather']['temperature_high']
            if session['weather']['temperature_low']:
                initialize['temperature_low'] = session['weather']['temperature_low']

        form = TemperatureSelectionForm(**initialize)
        return render_template('temperature_selection.html', form=form)

    def post(self):

        form = TemperatureSelectionForm()
        if form.validate_on_submit():

            weather = get_previous_selections()
            weather['temperature_high'] = form.temperature_high.data
            weather['temperature_low'] = form.temperature_low.data
            session['weather'] = weather

            return redirect(url_for('temperature_datalist'))
        else:
            return render_template('temperature_selection.html', form=form)


class TemperatureDataAsList(MethodView):

    def get(self):

        weather = session['weather']
        qs = create_queryset_for_temperature_as_list(weather)
        stations = format_dataset_for_list_views(qs)

        return render_template('temperature_listdata.html', weather=weather, stations=stations)


class AjaxGetStations(MethodView):

    def get(self, state):

        weather = get_previous_selections()
        stations = []
        queryset = Station.select().where(Station.attributes['State'] == state)
        for station in queryset:
            if station.attributes.get('Name'):
                stations.append({
                    "code": station.WBAN,
                    "name": station.attributes['Name']
                })
        return jsonify(select_option=weather['station'], stations=stations)
