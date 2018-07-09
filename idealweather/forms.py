from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.validators import DataRequired, Regexp, ValidationError, Email, Length, EqualTo
from models import Station


def validate_time_period(form, field):
    if field.data == '0':
        raise ValidationError('Select time period to be used for comparison.')


def validate_season(form, field):
    if form.time_period.data == 'season' and field.data == '0':
        raise ValidationError('Select a season.')


def validate_month(form, field):
    if form.time_period.data == 'month' and field.data == '0':
        raise ValidationError('Select a month.')


class HumiditySelectionForm(FlaskForm):
    time_period = SelectField('Time period',
                              validators=[validate_time_period],
                              choices=[('0', 'Select time period'), ('season', 'Season'), ('month', 'Month'), ],
                              description='Indicate if you want to select weather data based on a season or '
                                          'single month.',
                              )
    season = SelectField('Select season',
                         validators=[validate_season],
                         choices=[('0', 'Select season'),
                                  ('wi', 'Dec-Feb'),
                                  ('sp', 'Mar-May'),
                                  ('su', 'Jun-Aug'),
                                  ('au', 'Sep-Nov')],
                         description='Choose a season.',
                         )
    month = SelectField('Select month',
                        validators=[validate_month],
                        choices=[('0', 'Select month'),
                                 ('01', 'January'),
                                 ('02', 'February'),
                                 ('03', 'March'),
                                 ('04', 'April'),
                                 ('05', 'May'),
                                 ('06', 'June'),
                                 ('07', 'July'),
                                 ('08', 'August'),
                                 ('09', 'September'),
                                 ('10', 'October'),
                                 ('11', 'November'),
                                 ('12', 'December')],
                        description='Choose a month.',
                        )
    le20 = IntegerField('0% to 20% humidity',
                        description='Highest percent of humidity for this category you will accept.',
                        )
    lt40 = IntegerField('21% to 39% humidity',
                        description='Highest percent of humidity for this category you will accept.',
                        )
    target = IntegerField('40% to 60% humidity',
                          description='Highest percent of humidity for this category you will accept.',
                          )
    gt60 = IntegerField('61% to 79% humidity',
                        description='Highest percent of humidity for this category you will accept.',
                        )
    ge80 = IntegerField('80% to 100% humidity',
                        description='Highest percent of humidity for this category you will accept.',
                        )


def get_station_states():
    qs = Station.select(Station.attributes['State'].alias('state')).where(Station.attributes['State'] != 'None')\
        .order_by(Station.attributes['State']).distinct()
    choices = [('none', 'Please select'), ]
    for station in qs:
        choices.append((station.state, station.state))

    return choices


def validate_state(form, field):
    if field.data == 'none':
        raise ValidationError('A state or U.S. territory must be selected.')


def validate_station(form, field):
    field.errors = []
    wbans = []
    queryset = Station.select(Station.WBAN)
    for station in queryset:
        wbans.append(station.WBAN)
    if field.data == 'all':
        pass  # valid selection
    else:
        field_as_int = int(field.data)
        if field_as_int in wbans:
            pass  # valid selection
        else:
            raise ValidationError('Please make a valid selection.')


class StationSelectionForm(FlaskForm):

    state = SelectField('State', validators=[validate_state], choices=get_station_states(),
                        description='Select a state or U.S. territory.')
    station = SelectField('Station',
                          validators=[validate_station],
                          choices=[('all', 'All'),])


class TemperatureSelectionForm(FlaskForm):

    temperature_high = IntegerField('Average high', description='Enter the highest acceptable average temperature.')
    temperature_low = IntegerField('Average low', description='Enter the lowest acceptable average temperature.')
