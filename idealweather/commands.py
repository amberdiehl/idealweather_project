import csv
import os
# from os.path import isfile, join
import shutil

import click
from peewee import fn

from models import Station, Monthly, Humidity

from idealweather.config import APPLICATION_ROOT


EXCLUDE_MONTHLY_KEYS = ('WBAN', 'YearMonth', 'AvgDewPoint', 'AvgWetBulb', 'HDDSeasonToDate', 'CDDSeasonToDate',
                        'HDDSeasonToDateDeparture', 'CDDSeasonToDateDeparture', 'MeanStationPressure',
                        'MeanSeaLevelPressure', 'MaxSeaLevelPressure', 'DateMaxSeaLevelPressure',
                        'TimeMaxSeaLevelPressure', 'MinSeaLevelPressure', 'DateMinSeaLevelPressure',
                        'TimeMinSeaLevelPressure', 'Max12ZSnowDepth', 'DateMax12ZSnowDepth', 'MaxTempGE90Days',
                        'MaxTempLE32Days', 'MinTempLE32Days', 'MinTempLE0Days', 'ResultantWindSpeed',
                        'ResultantWindDirection', )


# Helper: Create attribute dictionary for model
def create_attribute_dict(row_dict, exclude_keys=None, exclude_values=None):

    object_attributes = {}

    if not exclude_keys:
        exclude_keys = ('WBAN', )

    if not exclude_values:
        exclude_values = ('YouWillNotFindThis', )

    for key, value in row_dict.iteritems():
        if value and key not in exclude_keys and value not in exclude_values:
            object_attributes[key] = value

    return object_attributes


# Return key based on humidity stratification
def get_key(rh):
    
    if rh < 0:
        return 'HumidityMissing'

    if rh <= 20:
        return 'HumidityLE20'
    
    if 20 < rh < 40:
        return 'HumidityLT40'
    
    if 40 <= rh <= 60:
        return 'HumidityTarget'

    if 60 < rh < 80:
        return 'HumidityGT60'

    if rh >= 80:
        return 'HumidityGE80'


# Analyze humidity data and return dict with results
def summarize_humidity_data(qs):

    data_summary = {}
    count = 0
    new_attributes = {}
    humidity_high = 0
    humidity_low = 100
    humidity_values = []

    for item in qs.objects().iterator():  # Each item is a day

        for key, value in item.readings.iteritems():

            # Get high, low relative humidity for the month and store values to calculate mean and median
            if value > -1:
                if value > humidity_high:
                    humidity_high = value
                if value < humidity_low:
                    humidity_low = value
                humidity_values.append(value)

            # Summarize values by counting instances based on 'buckets'
            count += 1
            humidity_bucket = get_key(value)
            if data_summary.get(humidity_bucket):
                data_summary[humidity_bucket] += 1
            else:
                data_summary.update({humidity_bucket: 1})

    # Pack results into dict to be included in monthly summary data
    if data_summary.get('HumidityMissing'):
        new_attributes['HumidityMissing'] = data_summary['HumidityMissing']

    count -= data_summary.get('HumidityMissing', 0)
    if count:
        new_attributes['HumidityCount'] = count
        for key, value in data_summary.iteritems():
            if not key == 'HumidityMissing':
                new_attributes[key] = float(data_summary[key]) / count

        new_attributes['HumidityHigh'] = humidity_high
        new_attributes['HumidityLow'] = humidity_low
        new_attributes['HumidityMean'] = float(sum(humidity_values)) / max(len(humidity_values), 1)

    if len(humidity_values) >= 3:
        middle = len(humidity_values) // 2
        sorted_humidity_values = sorted(humidity_values)
        if len(humidity_values) % 2: # if remainder, odd length
            new_attributes['HumidityMedian'] = sorted_humidity_values[middle]
        else:
            new_attributes['HumidityMedian'] = (sorted_humidity_values[middle] + sorted_humidity_values[middle-1]) / 2

    return new_attributes


# Helper: Print info regarding import
def print_totals(exists=None, added=None, rejected=None, message=None):
    if exists:
        click.echo('Already exists: {}'.format(exists))

    if added:
        click.echo('Added: {}'.format(added))

    if rejected:
        click.echo('Rejected: {}'.format(rejected))

    if message:
        click.echo('Message: {}'.format(message))

    click.echo('***')


# Import station file
def import_station_file(station_file):

    count_exists = 0
    count_added = 0
    count_rejected = 0

    with open(station_file, 'rb') as csv_file:

        csv_reader = csv.DictReader(csv_file, delimiter='|', quotechar='"')
        for row in csv_reader:

            if row['WBAN']:  # Ensure station code exists
                try:
                    Station.get(Station.WBAN == int(row['WBAN']))
                    count_exists += 1
                except Station.DoesNotExist:
                    Station.create(
                        WBAN=row['WBAN'],
                        attributes=create_attribute_dict(row)
                    )
                    count_added += 1
            else:
                count_rejected += 1

    print_totals(exists=count_exists, added=count_added, rejected=count_rejected)


# Import monthly weather data file
def import_monthly_file(file_path, file_name):

    count_added = 0
    count_rejected = 0

    monthly_file = file_path + '/' + file_name  # e.g. 201712monthly.txt
    modified_monthly_file = file_path + '/' + file_name.split('.')[0] + '_mod.txt'  # e.g. 201712monthly_mod.txt

    # Replace characters in column headings that cannot be used for dictionary keys
    with open(monthly_file) as from_file:
        line = from_file.readline()
        line = line.replace('<=', 'LE').replace('>=', 'GE').replace('.', 'x')

        with open(modified_monthly_file, mode="w") as to_file:
            to_file.write(line)
            shutil.copyfileobj(from_file, to_file)  # Copies from second line onward; innate to function

    with open(modified_monthly_file, 'rb') as csv_file:

        csv_reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:

            if row['WBAN']:  # Ensure station code exists

                attributes = create_attribute_dict(row, exclude_keys=EXCLUDE_MONTHLY_KEYS)

                humidity_year_month = fn.SUBSTR(Humidity.YearMonthDay, 1, 6)
                queryset = Humidity.select()\
                    .where((Humidity.WBAN == int(row['WBAN'])) & (humidity_year_month == row['YearMonth']))
                if queryset:  # If humidity data exists, summarize it to include in monthly model
                    new_attributes = summarize_humidity_data(queryset)
                    attributes.update(new_attributes)

                Monthly.create(
                    WBAN=row['WBAN'],
                    YearMonth=row['YearMonth'],
                    attributes=attributes
                )
                count_added += 1
            else:
                count_rejected += 1

    os.remove(modified_monthly_file)

    print_totals(added=count_added, rejected=count_rejected)


# Import monthly weather data file
def import_humidity_data(hourly_file):

    count_added = 0
    counter1 = 0
    counter2 = 0
    prior_wban = None
    prior_date = None
    readings = {}

    with open(hourly_file, 'rb') as csv_file:

        csv_reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:

            try:
                relative_humidity = int(row['RelativeHumidity'])
            except ValueError:  # Occurs when value is 'M', missing
                relative_humidity = -1

            if prior_wban:
                if not prior_wban == row['WBAN'] or not prior_date == row['Date']:
                    Humidity.create(
                        WBAN=prior_wban,
                        YearMonthDay=prior_date,
                        readings=readings
                    )
                    readings = {}
                    count_added += 1

            readings.update({'t' + row['Time']: relative_humidity})
            prior_wban = row['WBAN']
            prior_date = row['Date']

            counter1 += 1
            counter2 += 1
            if counter2 == 250000:
                click.echo('.', nl=False)
                counter2 = 0
                if counter1 == 1000000:
                    click.echo('|', nl=False)
                    counter1 = 0

    print_totals(added=count_added)


# Import weather history data for a given folder
# flask import_data QCLCD201712
@click.command()
@click.argument('folder')
def import_data(folder):

    data_path = APPLICATION_ROOT + '/raw_data/' + folder
    # import_files = [f for f in os.listdir(data_path) if isfile(join(data_path, f))]
    tag_file = data_path + '/' + 'imported.txt'

    try:

        with open(tag_file) as check_file:

            click.echo('\nNO IMPORT: This folder has already been imported.\n')
            check_file.close()

    except IOError:

        import_file = data_path + '/' + folder[5:] + 'station.txt'
        click.echo('Processing station.txt file...')
        import_station_file(import_file)

        import_file = data_path + '/' + folder[5:] + 'hourly.txt'
        click.echo('Processing hourly.txt file for humidity data...')
        import_humidity_data(import_file)

        import_file = folder[5:] + 'monthly.txt'
        click.echo('Processing monthly.txt file...')
        import_monthly_file(data_path, import_file)

        open(tag_file, 'a').close()


@click.command()
def list_weather():

    keys = ['HumidityLE20', 'HumidityLT40', 'HumidityTarget', 'HumidityGT60', 'HumidityGE80']
    month_map = ['Winter', 'Winter', 'Spring', 'Spring', 'Spring', 'Summer', 'Summer', 'Summer', 'Autumn', 'Autumn',
                 'Autumn', 'Winter']

    station_set = Station.select().order_by(Station.attributes['State'], Station.attributes['Name'])

    for station in station_set:

        if not station.attributes.get('State', 'n/a') == 'n/a':

            summary = {
                'Winter': {},
                'Spring': {},
                'Summer': {},
                'Autumn': {}
            }
            monthly_set = Monthly.select().where(Monthly.WBAN == station.WBAN)
            for month in monthly_set:
                if 'HumidityCount' in month.attributes.keys():
                    season = month_map[int(month.YearMonth[4:])-1]
                    for key in keys:
                        if key in month.attributes.keys():
                            if summary[season].get(key):
                                summary[season][key] += month.attributes[key]
                            else:
                                summary[season][key] = month.attributes[key]

            if summary['Winter']:
                click.echo('{} {}, {} {}'.format(station.WBAN,
                                                station.attributes.get('Name', 'n/a'),
                                                station.attributes['State'],
                                                summary['Winter']))
