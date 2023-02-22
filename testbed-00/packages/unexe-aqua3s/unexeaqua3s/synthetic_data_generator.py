import random
from datetime import datetime
from typing import List
import pandas as pd
import numpy as np

# Use same period for weekly_data_pattern_period and datapoll_period to avoid
# steps in data
# weekly_data_pattern_period = 15 * 60    # In seconds
weekly_data_pattern_period = 480 * 60    # In seconds


def _generate_weekly_data_pattern():
    global weekly_data_pattern_period
    num_timesteps = int(7 * 24 * 60 * 60 / weekly_data_pattern_period)
    start_date = pd.to_datetime('2020-01-01')
    dates = start_date + pd.to_timedelta(
        np.arange(num_timesteps) * weekly_data_pattern_period, 's')
    weekly_data_pattern = pd.DataFrame(dates, columns=['DateTime'])
    weekly_data_pattern['Day'] = weekly_data_pattern['DateTime'].apply(
        lambda x: x.dayofweek)
    weekly_data_pattern['Time'] = weekly_data_pattern['DateTime'].apply(
        lambda x: x.time())
    min_factor = []
    max_factor = []
    for _ in range(num_timesteps):
        factors = [random.uniform(0, 1), random.uniform(0, 1)]
        min_factor.append(min(factors))
        max_factor.append(max(factors))
    weekly_data_pattern['MinFactor'] = min_factor
    weekly_data_pattern['MaxFactor'] = max_factor
    grouped_weekly_data_pattern = weekly_data_pattern.groupby(['Day', 'Time'])
    return grouped_weekly_data_pattern


weekly_data_pattern = _generate_weekly_data_pattern()


def _timestep_normal_range(
        time_as_sec: int, weekly_min: float, weekly_max: float) -> List[float]:
    global weekly_data_pattern
    global weekly_data_pattern_period

    try:
        rounded_time_as_sec = weekly_data_pattern_period * round(time_as_sec/weekly_data_pattern_period)
        rounded_date_time = datetime.fromtimestamp(rounded_time_as_sec)
        day = rounded_date_time.weekday()
        time = rounded_date_time.time()

        #GARETH - this is a bit icky
        if time.hour == 0 or time.hour == 8 or time.hour == 16:
            pass
        else:
            time = time.replace(hour = ((((time.hour+1)%8)%3)*8) )

        pattern_factors = weekly_data_pattern.get_group((day, time))
        min_factor = pattern_factors['MinFactor'].tolist()[0]
        max_factor = pattern_factors['MaxFactor'].tolist()[0]
        weekly_range = weekly_max - weekly_min
        timestep_min = weekly_min + weekly_range * min_factor
        timestep_max = weekly_min + weekly_range * max_factor
        return timestep_min, timestep_max
    except Exception as e:
        print('_timestep_normal_range()-'+ str(e))



def synthetic_data(
        mode: str,
        time_as_sec: int,
        normal_min: float,
        normal_max: float,
        force_anomaly_high: bool = False,
        force_anomaly_low: bool = False,
        out_of_range_min: float = None,
        out_of_range_max: float = None) -> float:
    if mode == 'controlled_by_scenario':
        return synthetic_data_in_weekly_pattern(
            time_as_sec, normal_min, normal_max)
    if mode == 'controlled_by_scenario-in-anomaly':
        return synthetic_data_anomalous(
            time_as_sec, normal_min, normal_max, force_anomaly_high,
            force_anomaly_low)
    if mode == 'controlled_by_scenario-out of range':
        if not out_of_range_min:
            out_of_range_min = 0
        if not out_of_range_max:
            out_of_range_max = normal_min
        return synthetic_data_out_of_range(out_of_range_min, out_of_range_max)
    else:
        raise Exception('{} is not a valid mode'.format(mode))


def synthetic_data_in_weekly_pattern(
        time_as_sec: int, weekly_min: float, weekly_max: float) -> float:
    normal_min, normal_max = _timestep_normal_range(
        time_as_sec, weekly_min, weekly_max)
    return _random_value(normal_max, normal_min)


def _random_value(range_upper: float, range_lower: float) -> float:
    data_range = range_upper - range_lower
    mu = range_lower + data_range / 2
    sigma = data_range / 8
    return random.normalvariate(mu, sigma)


def synthetic_data_anomalous(
        time_as_sec: int, weekly_min: float, weekly_max: float,
        force_high: bool, force_low: bool) -> float:
    # Generate data within normal weekly range but outside normal range for
    # current day and time
    if force_high and force_low:
        raise Exception('Anomalous data generation cannot be forced high and '
                        'low simultaneously')
    normal_min, normal_max = _timestep_normal_range(
        time_as_sec, weekly_min, weekly_max)
    anomalous_high_value = _random_value(weekly_max, normal_max)
    anomalous_low_value = _random_value(normal_min, weekly_min)
    if force_high:
        return anomalous_high_value
    if force_low:
        return anomalous_low_value
    return random.choice([anomalous_high_value, anomalous_low_value])


def synthetic_data_out_of_range(lower: float, upper: float) -> float:
    return random.uniform(lower, upper)
