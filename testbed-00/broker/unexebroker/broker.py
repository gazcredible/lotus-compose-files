import os
import sqlite3
import inspect
import datetime
import unexefiware.time
import unexefiware.file
import unexefiware.base_logger
import json
import requests


class ContextBroker:
    def __init__(self, stellio_style=False):
        self.stream_table = 'stream_table'
        self.process_subscriptions = False
        self.logger = unexefiware.base_logger.BaseLogger()

        self.stellio_style = stellio_style

    def connect(self):
        return sqlite3.connect(self.DB_LOCATION, timeout=999.0)

    def init(self, logger=None, drop_all_tables=False):

        if logger:
            self.logger = logger

        try:
            if 'FILE_PATH' not in os.environ:
                raise Exception('FILE PATH not defined')

            path = os.environ['FILE_PATH']

            unexefiware.file.buildfilepath(path)

            self.DB_LOCATION = path + 'broker.sqlite3'

            db = self.connect()
            cursor = db.cursor()

            if drop_all_tables == True:
                if self.table_exists(cursor, self.stream_table) == True:
                    cursor.execute("SELECT * FROM " + self.stream_table, )

                    rows = cursor.fetchall()

                    for row in rows:
                        table_name = self.get_table_name(fiware_id=row[3], fiware_service=row[1])

                        if self.table_exists(cursor, table_name) == True:
                            cursor.execute("DROP TABLE " + table_name)
                            db.commit()

                    cursor.execute("DROP TABLE " + self.stream_table)
                    db.commit()

                cursor.execute(''' SELECT name FROM sqlite_master WHERE type='table' ''', )

                rows = cursor.fetchall()

                for row in rows:
                    table = str(row[0])
                    if table != 'sqlite_master':
                        cursor.execute("DROP TABLE " + table)

                db.commit()

            if self.table_exists(cursor, self.stream_table) == False:
                cursor.execute('CREATE TABLE ' + self.stream_table + ' (id INTEGER PRIMARY KEY, service TEXT, type TEXT, label TEXT) ')
                db.commit()
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

    def get_table_name(self, fiware_id, fiware_service):
        table_name = (fiware_service + '-' + fiware_id).lower()
        table_name = table_name.replace('-', '_')
        table_name = table_name.replace(':', '_')
        table_name = table_name.replace('+', '_')
        table_name = table_name.replace('.', '_')
        table_name = table_name.replace(' ', '_')

        return table_name

    def entity_in_stream(self, fiware_id, fiware_service):
        db = self.connect()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM " + self.stream_table + "  WHERE service = ? AND label = ?", (fiware_service, fiware_id))

        rows = cursor.fetchall()

        return len(rows) > 0

    def add_stream(self, fiware_id, fiware_service, fiware_type):
        db = self.connect()
        cursor = db.cursor()
        cursor.execute('INSERT INTO ' + self.stream_table + ' (service, type, label) VALUES (?,?,?)', (fiware_service, fiware_type, fiware_id))
        db.commit()

    def get_broker_data(self):
        data = {}

        try:
            db = self.connect()
            cursor = db.cursor()

            if self.table_exists(cursor, self.stream_table) == True:
                cursor.execute("SELECT * FROM " + self.stream_table)

                rows = cursor.fetchall()
                for row in rows:
                    if row[1] not in data:
                        data[row[1]] = {}

                    if row[2] not in data[row[1]]:
                        data[row[1]][row[2]] = []

                    data[row[1]][row[2]].append(row[3])

            return [200, data]

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

            return [500, str(e)]

        return [-1, []]


    def create_instance(self, json_data, fiware_service):

        if self.entity_in_stream(json_data['id'], fiware_service):
            # stream exists ??!
            self.logger.log(inspect.currentframe(), 'stream exists for: ' + fiware_service + ' ' + json_data['id'])
            return [404, 'stream exists for: ' + fiware_service + ' ' + json_data['id']]
        else:
            try:
                self.add_stream(fiware_id=json_data['id'], fiware_service=fiware_service, fiware_type=json_data['type'])

                table_name = self.get_table_name(json_data['id'], fiware_service)

                db = self.connect()
                cursor = db.cursor()

                if self.table_exists(cursor, table_name):
                    cursor.execute("DROP TABLE " + table_name)

                cursor.execute('CREATE TABLE ' + table_name + ' (id INTEGER PRIMARY KEY, date TEXT, timestamp INT, data TEXT) ')
                db.commit()

                result = []
                self.get_observedAt(json_data, result)

                date = datetime.datetime.now()

                if len(result) > 0:
                    date = unexefiware.time.fiware_to_datetime(result[0])

                self._add_entity(table_name, fiware_service, json_data, datetime_timestamp=date)

                if self.stellio_style:
                    for param in json_data:
                        if 'observedAt' in json_data[param]:
                            # add as temporal table
                            table_name = self.get_table_name(json_data['id'], fiware_service) + '_' + param

                            if self.table_exists(cursor, table_name):
                                cursor.execute("DROP TABLE " + table_name)

                            cursor.execute('CREATE TABLE ' + table_name + ' (id INTEGER PRIMARY KEY, date TEXT, timestamp INT, data TEXT) ')
                            db.commit()

                            self._add_entity(table_name, fiware_service, json_data[param], unexefiware.time.fiware_to_datetime(json_data[param]['observedAt']), db)
                            db.commit()

                return [201, '']
            except Exception as e:
                if self.logger:
                    self.logger.exception(inspect.currentframe(), e)

                return [500, str(e)]

        return [-1, '']

    # gareth - get the newest date in an entity
    def get_observedAt(self, root, result):
        for key in root:
            if isinstance(root[key], dict):
                self.get_observedAt(root[key], result)

            if key == 'observedAt':

                if len(result) == 0:
                    result.append(root[key])

                if root[key] > result[0]:
                    result[0] = root[key]

    def _add_entity(self, table_name, fiware_service, json_data, datetime_timestamp, db=None):

        try:
            fiware_date = unexefiware.time.datetime_to_fiware(datetime_timestamp)
            timestamp = int(unexefiware.time.datetime_to_timestamp(datetime_timestamp))

            if db == None:
                db = self.connect()
                cursor = db.cursor()
                cursor.execute('INSERT INTO ' + table_name + ' (date, timestamp, data) VALUES (?,?,?)', (fiware_date, timestamp, json.dumps(json_data)))
                db.commit()
            else:
                cursor = db.cursor()
                cursor.execute('INSERT INTO ' + table_name + ' (date, timestamp, data) VALUES (?,?,?)', (fiware_date, timestamp, json.dumps(json_data)))

            # is there a notification for this?
            if self.process_subscriptions:
                inst = self.get_type('Subscription', fiware_service)

                if inst > 0:
                    subs = self.get_by_index('Subscription', 0, inst, fiware_service)

                    session = requests.session()
                    if subs[0] == 200:
                        for sub in subs[1]:
                            for entity in sub['entities']:
                                if entity['type'] == json_data['type']:
                                    try:
                                        session.post(sub['notification']['uri'], data={'id': json_data['id'], 'fiware_service': fiware_service}, timeout=1)
                                    except Exception as e:
                                        self.logger.fail(inspect.currentframe(), str(e))
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

    def get_instance(self, fiware_id, fiware_service):
        table_name = self.get_table_name(fiware_id, fiware_service)

        db = self.connect()
        cursor = db.cursor()

        # if self.table_exists(cursor, table_name):
        try:
            # cursor.execute("SELECT date, data FROM " + table_name + "  ORDER BY timestamp desc LIMIT 1", )
            cursor.execute("SELECT date, data FROM " + table_name + "  ORDER BY id DESC LIMIT 1", )

            rows = cursor.fetchall()

            return [rows[0][0], json.loads(rows[0][1])]
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

        return ['', []]

    def get_temporal_instance(self, fiware_service, fiware_id, start_date, end_date):
        if self.stellio_style == True:
            return self.get_temporal_instance_stellio(fiware_service, fiware_id, start_date, end_date)
        else:
            return self.get_temporal_instance_orion(fiware_service, fiware_id, start_date, end_date)

    def get_temporal_instance_orion(self, fiware_service, fiware_id, start_date, end_date):
        results = []

        try:
            table_name = self.get_table_name(fiware_id, fiware_service)

            db = self.connect()
            cursor = db.cursor()

            cursor.execute("SELECT data FROM " + table_name + "  WHERE timestamp BETWEEN ? AND ?  order by timestamp asc"
                           , (int(unexefiware.time.fiware_to_time(start_date)), int(unexefiware.time.fiware_to_time(end_date))))

            rows = cursor.fetchall()

            for row in rows:
                results.append(json.loads(row[0]))
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

        return results

    def get_temporal_instance_stellio(self, fiware_service, fiware_id, start_date, end_date, fiware_attrs):

        # gareth -   Stellio style data has a single entity_id record and multiple entity_id<prop> tables
        #           So, find the table for the fiware_attr and SELECT from dates
        #           return {id, type, attr{ type, values:[data, value]}}, i.e. all the attrs are keys as part of the return dict/json

        results = {}

        try:

            db = self.connect()
            cursor = db.cursor()

            inst = self.get_instance(fiware_id, fiware_service)

            if inst[1] != []:
                results['id'] = fiware_id
                results['type'] = inst[1]['type']

                for key in fiware_attrs.split(','):
                    table_name = self.get_table_name(fiware_id, fiware_service) + '_' + key

                    cursor.execute("SELECT data FROM " + table_name + "  WHERE timestamp BETWEEN ? AND ?  order by timestamp asc"
                                   , (int(unexefiware.time.fiware_to_time(start_date)), int(unexefiware.time.fiware_to_time(end_date))))

                    rows = cursor.fetchall()

                    record = {}
                    results[key] = record
                    record['type'] = 'Property'
                    record['values'] = []

                    for row in rows:
                        data = json.loads(row[0])
                        try:
                            record['values'].append([data['value'], data['observedAt']])
                        except Exception as e:
                            self.logger.fail(inspect.currentframe(), str(e))

                    record['values'] = sorted(record['values'], key=lambda k: k[1])

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return results

    def update_instance(self, fiware_id, json_data, fiware_service):
        try:
            if self.stellio_style == True:
                self._update_instance_stellio(fiware_id, json_data, fiware_service)
            else:
                self._update_instance_orion(fiware_id, json_data, fiware_service)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def _update_instance_stellio(self, fiware_id, json_data, fiware_service):
        instance_data = self.get_instance(fiware_id, fiware_service)

        if instance_data[1] != []:
            table_name = self.get_table_name(fiware_id, fiware_service)
            db = self.connect()
            db = self.connect()
            cursor = db.cursor()

            for paramKey in json_data:
                # overwrite the data in instance_data with whatever's being updated in the patch
                # this is primarily for cases where patch data is partial (e.g. no unitCodes and stuff)
                # and also for anything that's not temporal
                # Temporal data will update the entire record in its table and the base entity table
                # Non-temporal data will update the base entity table

                data_to_write = json_data[paramKey]
                data_to_write = instance_data[1][paramKey]
                for key in json_data[paramKey]:
                    data_to_write[key] = json_data[paramKey][key]

                if 'observedAt' in json_data[paramKey]:
                    # create new entry for table+paramKey
                    param_table = table_name + '_' + paramKey

                    # is there a record for this time already? yes - update, no add
                    cursor.execute('SELECT data FROM ' + param_table + ' WHERE date = ?1',
                                   (json_data[paramKey]['observedAt'],))

                    rows = cursor.fetchall()

                    if len(rows) > 0:
                        # gareth -   copy existing parameters across from historic version
                        cursor.execute('UPDATE ' + param_table + ' SET data =?1 WHERE date = ?2',
                                       (json.dumps(data_to_write), data_to_write['observedAt'],))
                        db.commit()
                    else:
                        self._add_entity(param_table, fiware_service, data_to_write,
                                         datetime_timestamp=unexefiware.time.fiware_to_datetime(
                                             data_to_write['observedAt']), db=db)

            # update table
            cursor.execute('UPDATE ' + table_name + ' SET data =?1 WHERE id = (SELECT MAX(id) FROM ' + table_name + ')',
                           (json.dumps(instance_data[1]),))
            db.commit()
        else:
            raise Exception('failure')

    def _update_instance_orion(self, fiware_id, json_data, fiware_service):

        try:
            instance_data = self.get_instance(fiware_id, fiware_service)

            if instance_data[1] != []:
                table_name = self.get_table_name(fiware_id, fiware_service)
                key = list(json_data.keys())[0]

                if key in instance_data[1]:
                    instance_data[1][key] = json_data[key]

                    result = []
                    self.get_observedAt(json_data, result)

                    date = datetime.datetime.now()

                    # gareth -   If we have an observedAt date for the patch data
                    #           and the date is not the same as the current record
                    #           create a new entity from that data
                    #
                    #           However, if we don't have an observedAt date or the dates are the same, just update the current record
                    #

                    if len(result) > 0 and instance_data[0] != result[0]:
                        date = unexefiware.time.fiware_to_datetime(result[0])
                        self._add_entity(table_name, fiware_service, instance_data[1], datetime_timestamp=date)
                    else:
                        # gareth -   update existing record
                        db = self.connect()
                        cursor = db.cursor()
                        cursor.execute('UPDATE ' + table_name + ' SET data =?1 WHERE id = (SELECT MAX(id) FROM ' + table_name + ')', (json.dumps(instance_data[1]),))
                        db.commit()

                    return [204, '']  # as defined
                else:
                    return [500, 'something else went wrong']
            else:
                return [500, 'something went wrong']
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

            return [500, 'failed!' + str(e)]

    def update_instances(self, fiware_id, json_data, fiware_service):

        try:
            instance_data = self.get_instance(fiware_id, fiware_service)

            if instance_data[1] != []:
                table_name = self.get_table_name(fiware_id, fiware_service)

                db = self.connect()
                for inst in json_data:

                    key = list(inst.keys())[0]

                    if key in instance_data[1]:
                        instance_data[1][key] = inst[key]

                        result = []
                        self.get_observedAt(inst, result)

                        date = datetime.datetime.now()

                        if len(result) > 0:
                            date = unexefiware.time.fiware_to_datetime(result[0])

                        self._add_entity(table_name, fiware_service, instance_data[1], datetime_timestamp=date, db=db)

                db.commit()

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

    def delete_instance(self, fiware_id, fiware_service):

        try:
            db = self.connect()
            cursor = db.cursor()

            if self.entity_in_stream(fiware_id, fiware_service):
                # remove from stream table
                cursor.execute("DELETE FROM " + self.stream_table + " WHERE service = ?1 AND label = ?2", (fiware_service, fiware_id))
                db.commit()

            table_name = self.get_table_name(fiware_id, fiware_service)

            # drop table
            if self.table_exists(cursor, table_name) == True:
                cursor.execute("DROP TABLE " + table_name)
                db.commit()
                return [200, '']

            return [404, 'Entity does not exist:' + fiware_service + ' ' + fiware_id]
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

            return [500, 'Internal Error:' + fiware_service + ' ' + fiware_id + ' ' + str(e)]

    def get_type(self, type, fiware_service):
        # get from stream_table -> return count
        db = self.connect()
        cursor = db.cursor()

        cursor.execute("SELECT label FROM " + self.stream_table + "  WHERE service = ? AND type = ?", (fiware_service, type))

        rows = cursor.fetchall()

        return len(rows)

    def get_by_index(self, type, index, limit, fiware_service):
        result = []

        db = self.connect()
        cursor = db.cursor()

        cursor.execute("SELECT label FROM " + self.stream_table + "  WHERE service = ? AND type = ?", (fiware_service, type))

        entries = cursor.fetchall()

        for i in range(index, index + limit):

            table_name = self.get_table_name(entries[i][0], fiware_service)

            try:
                cursor.execute("SELECT data FROM " + table_name + "  WHERE id = (SELECT MAX(id)  FROM " + table_name + ")", )

                rows = cursor.fetchall()

                result.append(json.loads(rows[0][0]))
            except Exception as e:
                if self.logger:
                    self.logger.exception(inspect.currentframe(), e)

                return [500, []]

        return [200, result]

    def table_exists(self, cursor, name):
        cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', (name,))

        # if the count is 1, then table exists
        if cursor.fetchone()[0] == 1:
            return True
        else:
            return False