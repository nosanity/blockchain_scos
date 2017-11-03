# coding: utf-8

import datetime
import logging
import re
from django.conf import settings
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import RequestException


class InfluxQueryHandler(object):
    def __init__(self):
        self.client = InfluxDBClient(**settings.INFLUX_DATABASE_SETTINGS)
        self.SERIE_NAME = 'status'
        self.OFFLINE_TIMEOUT = '1h'
        self.DELTA = '1s'
        self._DELTA = datetime.timedelta(seconds=1)

    def _query(self, query):
        try:
            return self.client.query(query)
        except (InfluxDBClientError, InfluxDBServerError, RequestException) as e:
            logging.error(u'Influx query failed, query: %s, exception: %s' % (query, e))

    def _get_first_row(self, query):
        res = self._query(query)
        if not res:
            return
        try:
            data = res.get_points().next()
        except StopIteration:
            return
        return data

    def get_nodes_count(self):
        """
        сколько нод подключено к блокчейну
        """
        return self._get_first_row("select * from {} where type='connections' order by time desc limit 1".
                                   format(self.SERIE_NAME))

    def get_master_entries_count(self, time):
        """
        сколько блоков на мастер ноде
        """
        return self._get_first_row("select * from {serie} where type='blockcount' and time > '{time}' - {delta} and time < '{time}' + {delta} order by time desc limit 1".
                                   format(serie=self.SERIE_NAME, time=time, delta=self.DELTA))

    def get_node_names(self):
        """
        получение имен всех использованных нод через парсинг series
        """
        res = self._query("show series")
        if not res:
            return
        names = set()
        for item in res.get_points():
            data = item.get('key', '').split(',')
            if not data or not data[0] == self.SERIE_NAME:
                continue
            tags = data[1:]
            if not tags:
                continue
            tags = dict([tuple(i.split('=')) for i in tags])
            if tags.get('type') == 'synced_blocks' and tags.get('host'):
                names.add(tags['host'])
        return names

    def get_nodes_state(self, master_cnt, all_nodes, time):
        """
        получение статусов нод
        :param master_cnt: количество блоков на мастер ноде
        :param all_nodes: имена нод
        :return: list
        """
        res = self._query("select * from {} where type='synced_blocks' and time > now() - {} order by time desc".
                          format(self.SERIE_NAME, self.OFFLINE_TIMEOUT))
        if not res:
            return
        nodes = {}
        for point in res.get_points():
            node = point.get('host')
            value = point.get('value')
            if node not in nodes and point.get('time') and self._is_close(time, point['time']):
                nodes[node] = value
        all_nodes = sorted(all_nodes)
        return [
            {
                'name': i,
                'state': 'OFFLINE' if i not in nodes else ('UNSYNC' if nodes[i] < master_cnt else 'SYNC')
            }
            for i in all_nodes
        ]

    def _is_close(self, t1, t2):
        """
        проверка типа |a - b| <= eps
        """
        _t1 = self._to_dt(t1)
        _t2 = self._to_dt(t2)
        return _t1 - self._DELTA <= _t2 <= _t1 + self._DELTA

    def _to_dt(self, time):
        """
        перевод строки с наносекундами в datetime с точностью до микросекунд
        """
        nanoseconds = re.search(r'\.(\d+)Z$', time).group(1)
        microseconds = round(float(nanoseconds) / 10**9, 6) * 10**6
        new_time = re.sub(r'\.(\d+)Z$', '.%dZ' % microseconds, time)
        return datetime.datetime.strptime(new_time, '%Y-%m-%dT%H:%M:%S.%fZ')

    def get_info(self):
        """
        получение информации о количестве подключенных нод и их статусах
        :return: dict
        """
        names = self.get_node_names()
        data = self.get_nodes_count()
        cnt, time = data.get('value'), data.get('time')
        if not time:
            return
        data = self.get_master_entries_count(time)
        master_cnt = data.get('value')
        if names is not None and cnt is not None and master_cnt is not None:
            state = self.get_nodes_state(master_cnt, names, time)
            if not state:
                return
            return {
                'nodes_count': cnt,
                'state': state
            }
