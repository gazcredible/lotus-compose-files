import unexefiware.time
import unexeaqua3s.deviceinfo
import unexefiware.base_logger
import inspect
import os
import sys

class Bucketiser:
    def __init__(self):
        self.buckets = []

        for i in range(0, 21):
            entry = {}
            entry['results'] = []
            self.buckets.append(entry)

    def timestamp_to_bucket(self, fiware_datetime):
        # return (day of week *3) + (hour/8)
        try:
            date = unexefiware.time.fiware_to_datetime(fiware_datetime)

            index = int(date.strftime('%w')) * 3
            index += int((date.hour) / 8)

            return self.buckets[index]
        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)

    def add(self, value, observedAt):

        if value < 99999:
            self.timestamp_to_bucket(observedAt)['results'].append(value)

    def generate_results(self):
        results = []

        try:
            for bucket in self.buckets:
                record = {}
                record['min'] = sys.float_info.max
                record['max'] = sys.float_info.min
                record['average'] = 0

                if bucket['results']:
                    record['min'] = min(bucket['results'])
                    record['max'] = max(bucket['results'])
                    record['average'] = round(sum(bucket['results']) / len(bucket['results']), 3)
                else:
                    record['min'] = 0
                    record['max'] = 0

                results.append(record)
        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)

        return results

def build_limit(fiware_service, device, fiware_time):

    start_time = '2022-04-01T00:00:00Z'
    end_time = fiware_time

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

    data = fiware_wrapper.get_temporal_orion(fiware_service, device['id'], start_time, end_time)

    bucketiser = Bucketiser()

    if len(data)> 0 and data[0] != -1:
        for entry in data:
            try:
                if 'value' in entry:
                    bucketiser.add(float(entry['value']), entry['observedAt'])
                else:
                    # gareth - this is for oldie stylee data
                    prop = entry['controlledProperty']['value']
                    bucketiser.add(float(entry[prop]['value']), entry[prop]['observedAt'])
            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(), e)

    return bucketiser.generate_results()
