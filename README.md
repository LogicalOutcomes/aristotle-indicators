# Indicators Extension
An Aristotle (1.5) Extension to manage indicators

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

## Importing data from xlsx files:

Financial indicators:
```
./manage.py import_financial_indicators <path-to-xlsx-file> --collection 'Financial collection'
```

DHIS2 indicators:
```
./manage.py import_dhis2_indicators <path-to-xlsx-file> --collection 'DHIS2 collection'
```

This process might take some minutes depending on your file
