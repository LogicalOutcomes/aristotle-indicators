# Indicators Extension
An Aristotle (1.5) Extension to manage indicators

[![Build Status](https://travis-ci.org/LogicalOutcomes/aristotle-indicators.svg?branch=master)](https://travis-ci.org/LogicalOutcomes/aristotle-indicators)
[![Coverage Status](https://coveralls.io/repos/github/LogicalOutcomes/aristotle-indicators/badge.svg?branch=master)](https://coveralls.io/github/LogicalOutcomes/aristotle-indicators?branch=master)

## Installation

Install this repo with pip.
```
-e git+git://github.com/LogicalOutcomes/aristotle-indicators@master#egg=aristotle-indicators
```

Add it to your `INSTALLED_APPS`:

```
INSTALLED_APPS = (
    'indicators',
...
)
```

Migrate your site:

```
./manage.py migrate indicators
```

## Management commands to Importing data from xlsx files:

Financial indicators:
```
./manage.py import_financial_indicators <path-to-xlsx-file> --collection 'Financial collection'
```

DHIS2 indicators:
```
./manage.py import_dhis2_indicators <path-to-xlsx-file> --collection 'DHIS2 collection'
```

This process might take some minutes depending on your file


## Interface commands to import  data from xlsx files:

The UI uses `celery` to run the task in an async way. If you are not using celery you can add `CELERY_TASK_ALWAYS_EAGER = True` to your `settings.py`.

To include the import dashboard to the Admin tools you need to extend the Aristotle Settings with this addons:

```
ARISTOTLE_SETTINGS['DASHBOARD_ADDONS'] = ['indicators']
```
