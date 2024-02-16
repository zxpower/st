"""
Smart electricity meter consumption data scraper for e-st.lv
"""

import json
import argparse
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
import requests
from pyquery import PyQuery


class STScraper:
    """
    Smart electricity meter consumption data scraper class for e-st.lv
    """

    BASE_HOST = 'https://mans.e-st.lv'
    LOGIN_URL = BASE_HOST + '/lv/private/user-authentification/'
    DATA_URL = BASE_HOST + '/lv/private/paterini-un-norekini/paterinu-grafiki/'

    # Data url parameters

    PERIOD_DAY = 'D'
    PERIOD_MONTH = 'M'
    PERIOD_YEAR = 'Y'

    GRANULARITY_HOUR = 'H'
    GRANULARITY_DAY = 'D'

    def __init__(self, login, password, object_id, meter_id):
        """
        Class initialisation

        :param login: username
        :param password: user password
        :param meter_id: object EIC ID
        :param meter_id: smart meter ID
        """
        self.login = login
        self.password = password
        self.object_id = object_id
        self.meter_id = meter_id

        self.session = requests.Session()

    def _get_current_date(self):
        """Get the current year, month, and day as a dictionary."""
        now = datetime.now()
        return {'year': now.strftime('%Y'), 'month': now.strftime('%m'), 'day': now.strftime('%d')}

    def _get_current_year(self):
        """
        Get the current year e.g. 2024
        """
        return self._get_current_date()['year']

    def _get_current_month(self):
        """
        Get the current month e.g. 02
        """
        return self._get_current_date()['month']

    def _get_current_day(self):
        """
        Get the current day e.g. 14
        """
        return self._get_current_date()['day']

    def _get_data_url(self, period=None, year=None, month=None, day=None, granularity=None):
        """
        Prepare data url depending on request type and parameters

        :param period: report time period
        :type period: str | should be one of self.PERIOD_<*>
        :param year: year
        :type year: str | None
        :param month: month
        :type month: str | None
        :param day: day
        :type day: str | None
        :param granularity: report data type
        :type granularity: str | should be one of self.GRANULARITY_<*>

        :return: generated data url
        """

        params = {
            'objectEic': self.object_id,
            'counterNumber': self.meter_id,
            'period': period
        }

        year = year or self._get_current_year()

        if period == self.PERIOD_YEAR:
            params['year'] = year

        if period == self.PERIOD_MONTH:
            params['year'] = year
            params['month'] = month or self._get_current_month()
            params['granularity'] = granularity

        if period == self.PERIOD_DAY:

            month = month or self._get_current_month()
            day = day or self._get_current_day()

            params['date'] = '{0}.{1}.{2}'.format(day, month, year)
            params['granularity'] = granularity

        print(self.DATA_URL + '?' + urlencode(params))
        return self.DATA_URL + '?' + urlencode(params)

    @staticmethod
    def _format_timestamp(timestamp):
        """
        Convert JS timestamp to human readable date and time

        :param timestamp: timestamp
        :return: datetime e.g. 2024-02-14 02:00:00
        :rtype: str
        """
        return datetime.fromtimestamp(
            int(timestamp) / 1000.0, tz=timezone(timedelta(hours=0))
        ).strftime('%Y-%m-%d %H:%M:%S')

    def _format_response(self, response_data, neto=True):
        """
        Parse out the real data from graph json

        :param response_data: graph json source
        :return: parsed data
        """
        response_cons_data = response_data['values']['A+']['total']['data']
        response_neto_data = response_data['values']['A-']['total']['data']

        cons_data = [{
            'data': self._format_timestamp(item['timestamp']),
            'value': item['value']
        } for item in response_cons_data]

        if neto:
            neto_data = [{
                'data': self._format_timestamp(item['timestamp']),
                'value': item['value']
            } for item in response_neto_data]

            data = {
                'A+': cons_data,
                'A-': neto_data
            }
        else:
            data = cons_data

        return data

    def get_day_data(self, neto=True, year=None, month=None, day=None):
        """
        Get the data of the specified day

        :param year:
        :param month:
        :param day:
        :return:
        """
        response = self._fetch_remote_data(period=self.PERIOD_DAY, month=month,
                                           year=year, day=day,
                                           granularity=self.GRANULARITY_HOUR)
        return self._format_response(response, neto)

    def get_month_data(self, neto=True, year=None, month=None):
        """
        Get the data of the specified month

        :param year:
        :param month:
        :return:
        """
        response = self._fetch_remote_data(period=self.PERIOD_MONTH, month=month, year=year,
                                           granularity=self.GRANULARITY_DAY)
        return self._format_response(response, neto)

    def get_year_data(self, neto=True, year=None):
        """
        Get the data of the specified year

        :param year:
        :return:
        """
        response = self._fetch_remote_data(period=self.PERIOD_YEAR, year=year)
        return self._format_response(response, neto)

    def _fetch_remote_data(self, **kwargs):
        """
        Do authentification and retrieve the data

        :param kwargs:
        :return:
        """
        response = self.session.get(self._get_data_url(**kwargs))
        root = PyQuery(response.text)

        fields = (
            '_token',
            'returnUrl',
            'login',
            'password'
        )

        values = {}
        for field in fields:
            #values[field] = root('input[name={0}]'.format(field)).attr('value')
            values[field] = root(f'input[name={field}]').attr('value')

        values['login'] = self.login
        values['password'] = self.password

        response = self.session.post(self.LOGIN_URL, data=values)
        root = PyQuery(response.text)
        values = root('div.chart').attr('data-values')
        return json.loads(values)


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
        description='mans.e-st.lv electricity consumption data scraper'
    )
    parser.add_argument('--username', default=None, help='Website username')
    parser.add_argument('--password', default=None, help='Website password')
    parser.add_argument('--objectid', default=None, help='Object ID')
    parser.add_argument('--meter', default=None, help='Electricity meter ID')
    parser.add_argument('--period', default='month', help='Report data time period')
    parser.add_argument('--year', default=None)
    parser.add_argument('--month', default=None)
    parser.add_argument('--day', default=None)
    parser.add_argument('--neto', default=True, help="Include generation data")
    parser.add_argument('--outfile', default=None, help='Save data in specified file')
    opts = parser.parse_args()

    if not opts.username or not opts.password:
        raise TypeError('Username and/or password must be set')

    if not opts.objectid:
        raise TypeError('Object ID must be set')

    if not opts.meter:
        raise TypeError('Electricity meter ID must be set')

    scraper = STScraper(opts.username, opts.password, opts.objectid, opts.meter)

    # Adjusted call to data retrieval methods based on selected period
    if opts.period == 'year':
        data = scraper.get_year_data(opts.neto, opts.year)
    elif opts.period == 'month':
        data = scraper.get_month_data(opts.neto, opts.year, opts.month)
    elif opts.period == 'day':
        data = scraper.get_day_data(opts.neto, opts.year, opts.month, opts.day)
    else:
        raise ValueError("Invalid period specified")

    if opts.outfile:
        with open(opts.outfile, 'w', encoding="utf8") as f:
            json.dump(data, f, indent=4)
    else:
        print(json.dumps(data, indent=4))


if __name__ == '__main__':
    main()
