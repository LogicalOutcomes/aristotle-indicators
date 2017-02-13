# Indicators Extension
An Aristotle Extension to manage indicators

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
