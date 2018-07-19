# iDeal Weather, a simple Flask App

Copyright 2018 Amber Diehl.

The iDeal weather app allows a user to locate their ideal location in the
United States based on U.S. government collected weather data.

This is in contrast to most other sites where one must provide a location
to see its weather data. This sets up a "hunt and peck" approach trying
to locate a town that has the characteristics of a person's ideal weather.

This initial version of the app allows for searching based on temperature
and humidity.

A user provides their search criteria based on a percent of tolerance. Using
humidity as an example, humidity raw data has been pre-processed and summarized
into 5 categories:

- 0 to 20 percent, extremely low
- 21 to 39 percent, low
- 40 to 60 percent, moderate
- 61 to 79 percent, high
- 80 to 100 percent, extremely high

A person can search based on humidity where a given percentage
of humidity readings fall within their tolerance. In other words, a person
can search on criteria that says: show me cities where X, Y, Z months average
a moderate level of humidity 80% of the time or more.

The management command enables importing as many months of data as desired.
Humidity readings, if collected by a weather station, are collected at
least hourly, and at times even more frequently. Station humidity files
contain about 7 million records. These are processed in approximately
30 to 40 seconds (on my local machine). The processing speed is attained by
summarizing humidity data for a given period in memory and only writing
to the model, storing the summarized humitity data in a JSON field. Searches
using the JSON field perform very well.

One additional search is planned, enabling trending (assuming more years
are imported), along with adding graphical representation of the search
results.
