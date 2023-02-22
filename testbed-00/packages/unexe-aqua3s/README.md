# README

## Setup

1. Create and activate a virtual environment in the project folder, e.g.:
    * `virtualenv venv`
    * `source venv/bin/activate` or `source venv/Scripts/activate`
2. Install requirements:
    * `pip install -r requirements.txt`


## Creating a wheel

1. Increment version number in `setup.py`
2. Generate wheel:
    * `python setup.py sdist bdist_wheel`

## Using wheel

1. Install from wheel (replacing `x.x.x` with the required version):
    * `pip install dist/<module>-x.x.x-py3-none-any.whl`

## Running tests

1. Install from wheel, as above
2. Run tests:
    * `pytest`
