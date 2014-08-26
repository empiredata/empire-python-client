#!/usr/bin/python
"""
Empire command-line client tests
"""
import json
import unittest
from empire.client import EmpireException

import httmock

from empire import Empire


class FakeConnection(object):
    def close(self):
        pass


class EmpireTest(unittest.TestCase):
    json_headers = {'content-type': 'application/json'}

    def setUp(self):
        self.empire = Empire(appkey="MOCK_USER", api_server='api.empire.co')
        self.services = {}

    def mock_response_200(self, request, data):
        headers = {}

        if not isinstance(data, basestring):
            data = json.dumps(data)
            headers = self.json_headers

        response = httmock.response(200, data, headers, None, 5, request)
        setattr(response, 'connection', FakeConnection())
        return response

    def mock_response_500(self, request, message):
        response = httmock.response(500, message, {}, None, 5, request)
        setattr(response, 'connection', FakeConnection())
        return response

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/session/create')
    def session_create_mock(self, url, request):
        return self.mock_response_200(request, {'status': 'OK', 'sessionkey': 'TESTSESSION'})

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/services/salesforce/connect')
    def connect_mock(self, url, request):
        data = json.loads(request.body)
        self.services['salesforce'] = data
        return self.mock_response_200(request, {'status': 'OK'})

    def test_connect(self):
        sf_data = {
            "access_token": "MOCK_ACCESS_TOKEN",
            "client_id": "MOCK_CLIENT",
            "refresh_token": "MOCK_REFRESH_TOKEN",
            "endpoint": "https://na15.salesforce.com"
        }

        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.connect_mock):
                self.empire.connect("salesforce", sf_data)

        self.assertEqual(self.services['salesforce'], sf_data)

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/services')
    def describe_all_mock(self, url, request):
        return self.mock_response_200(request, {'status': 'OK', "name": "salesforce"})

    def test_describe_all(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.describe_all_mock):
                services_data = self.empire.describe()

        self.assertEqual(services_data, {'status': 'OK', "name": "salesforce"})

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/services/salesforce')
    def describe_one_mock(self, url, request):
        return self.mock_response_200(request, {'status': 'OK', "name": "salesforce", "tables": ["table1"]})

    def test_describe_one(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.describe_one_mock):
                service_data = self.empire.describe("salesforce")

        self.assertEqual(service_data, {'status': 'OK', "name": "salesforce", "tables": ["table1"]})

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/services/salesforce/table1')
    def describe_table_mock(self, url, request):
        return self.mock_response_200(request, {'status': 'OK', "name": "table1"})

    def test_describe_table(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.describe_table_mock):
                service_data = self.empire.describe("salesforce", "table1")

        self.assertEqual(service_data, {'status': 'OK', "name": "table1"})

    def test_describe_table_without_service(self):
        self.assertRaises(ValueError, self.empire.describe, None, "table1")

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/services/salesforce/table1')
    def describe_table_broken_mock(self, url, request):
        return self.mock_response_500(request, "Something is broken")

    def test_describe_broken(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.describe_table_broken_mock):
                self.assertRaises(EmpireException, self.empire.describe, "salesforce", "table1")

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/query')
    def query_mock(self, url, request):
        return self.mock_response_200(request, 'QUERY\nRESULT')

    def test_query(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.query_mock):
                query_result = list(self.empire.query('SELECT * FROM salesforce_account'))

        self.assertEqual(query_result, ['QUERY', 'RESULT'])

    @httmock.urlmatch(netloc='api.empire.co', path='/empire/view')
    def view_mock(self, url, request):
        if request.method == 'POST':
            if json.loads(request.body) == {'name': 'view', 'query': 'SELECT QUERY'}:
                return self.mock_response_200(request, {'status': 'OK'})

        if request.method == 'PUT':
            if json.loads(request.body) == {'name': 'view'}:
                return self.mock_response_200(request, {'status': 'OK'})

        if request.method == 'DELETE':
            if json.loads(request.body) == {'name': 'view'}:
                return self.mock_response_200(request, {'status': 'OK'})

        return self.mock_response_500(request, "Something is broken")

    def test_create_view(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.view_mock):
                r = self.empire.create_view(name='view', sql='SELECT QUERY')

        self.assertEqual(r, {'status': 'OK'})

    def test_refresh_view(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.view_mock):
                r = self.empire.refresh_view(name='view')

        self.assertEqual(r, {'status': 'OK'})

    def test_drop_view(self):
        with httmock.HTTMock(self.session_create_mock):
            with httmock.HTTMock(self.view_mock):
                r = self.empire.drop_view(name='view')

        self.assertEqual(r, {'status': 'OK'})

