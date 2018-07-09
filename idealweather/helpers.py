from models import Station, Monthly


def create_queryset_for_humidity_as_list(weather):

    queryset = Monthly.select().join(Station, on=(Station.WBAN == Monthly.WBAN)).where(
        (Monthly.YearMonth << weather['months']) &
        (Monthly.attributes.contains('HumidityCount')) &
        (
                (Monthly.attributes['HumidityLE20'] >> None) |
                (Monthly.attributes['HumidityLE20'].cast('float') <= weather['percentage']['le20'])
        ) &
        (
                (Monthly.attributes['HumidityLT40'] >> None) |
                (Monthly.attributes['HumidityLT40'].cast('float') <= weather['percentage']['lt40'])
        ) &
        (
                (Monthly.attributes['HumidityTarget'] >> None) |
                (Monthly.attributes['HumidityTarget'].cast('float') <= weather['percentage']['target'])
        ) &
        (
                (Monthly.attributes['HumidityGT60'] >> None) |
                (Monthly.attributes['HumidityGT60'].cast('float') <= weather['percentage']['gt60'])
        ) &
        (
                (Monthly.attributes['HumidityGE80'] >> None) |
                (Monthly.attributes['HumidityGE80'].cast('float') <= weather['percentage']['ge80'])
        )
    ).order_by(Station.attributes['State'], Station.attributes['Name'], Monthly.WBAN, Monthly.YearMonth)

    return queryset


def create_queryset_for_station_as_list(weather):

    queryset = Monthly.select().join(Station, on=(Station.WBAN == Monthly.WBAN)).where(
        (Station.attributes['State'] == weather['state'])
    ).order_by(Station.attributes['State'], Station.attributes['Name'], Monthly.WBAN, Monthly.YearMonth)

    if not weather['station'] == 'all':
        queryset = queryset.where((Station.WBAN == weather['station']))

    return queryset


def create_queryset_for_temperature_as_list(weather):

    queryset = Monthly.select().join(Station, on=(Station.WBAN == Monthly.WBAN)).where(
        (
                (Monthly.attributes['AvgMaxTemp'] != 'M') &
                (Monthly.attributes['AvgMaxTemp'].cast('float') <= weather['temperature_high'])
        ) &
        (
                (Monthly.attributes['AvgMinTemp'] != 'M') &
                (Monthly.attributes['AvgMinTemp'].cast('float') >= weather['temperature_low'])
        )
    ).order_by(Station.attributes['State'], Station.attributes['Name'], Monthly.WBAN, Monthly.YearMonth)

    return queryset


def pack_station_for_list_views(wban, months):

    station = Station.get(Station.WBAN == wban)
    station_data = {'wban': station.WBAN}
    station_data['name'] = station.attributes.get('Name', 'n/a')
    station_data['state'] = station.attributes.get('State', 'n/a')
    station_data['station_data'] = months

    return station_data


def format_dataset_for_list_views(queryset):

    buckets = ['HumidityLE20', 'HumidityLT40', 'HumidityTarget', 'HumidityGT60', 'HumidityGE80']
    prior_wban = None
    stations = []
    months = []
    for station_month in queryset:
        if prior_wban and not prior_wban == station_month.WBAN:
            stations.append(pack_station_for_list_views(prior_wban, months))
            months = []

        month_data = {'month': station_month.YearMonth[4:]}
        month_data['humidity'] = []
        for bucket in buckets:
            humidity = station_month.attributes.get(bucket, 'M')
            if type(humidity) is float:
                humidity = str(humidity)[:4]
            month_data['humidity'].append((bucket[8:], humidity))
            month_data['temperature_high'] = station_month.attributes.get('AvgMaxTemp', 'M')
            month_data['temperature_low'] = station_month.attributes.get('AvgMinTemp', 'M')
            month_data['temperature_avg'] = station_month.attributes.get('AvgTemp', 'M')
        months.append(month_data)

        prior_wban = station_month.WBAN

    if queryset:
        if len(queryset) == 1:
            stations.append(pack_station_for_list_views(queryset[0].WBAN, months))
        else:
            stations.append(pack_station_for_list_views(station_month.WBAN, months))  # catch the last one

    return stations
