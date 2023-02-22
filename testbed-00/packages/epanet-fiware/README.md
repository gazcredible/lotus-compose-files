# README

## Setup

1. Create and activate a virtual environment in the project folder, e.g.:
    * `virtualenv venv`
    * `source venv/bin/activate` or `source venv/Scripts/activate`
2. Install requirements:
    * `pip install -r requirements.txt`


## Creating an epanet_-_fiware wheel

1. Increment version number in `setup.py`
2. Generate wheel:
    * `python setup.py sdist bdist_wheel`

## Using wheel

1. Install epanet_fiware from wheel (replacing `x.x.x` with the required version):
    * `pip install dist/epanet_fiware-x.x.x-py3-none-any.whl`
2. Example usage of the epanet_fiware module is given in `run_analysis.py`. To run a simulation using net1.inp and extract some model properties, for example, do: `python ./run_analysis.py ./inputs/net1.inp outputs`. To store the model using FIWARE, and retrieve in a separate instance, add a `--fiware` flag. To use FIWARE, the `config.py` file should be updated with the server details (`client_id`, `client_secret` and `auth_url` can be left as `None` if not required).

## Running tests

1. Install epanet_fiware from wheel, as above
2. Run tests:
    * `pytest`
