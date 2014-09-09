#!/usr/bin/python
"""
Empire command-line client
"""

import sys
import json
import urllib
import time

import requests
import pyaml
import pager
import dateutil.parser

class EmpireException(Exception):
    pass

class Empire(object):
    def __init__(self, appkey=None, enduser=None, api_server='api.empiredata.co', secrets_yaml=None):
        """
        appkey is your Empire application key, and is necessary for using the API.
        enduser is an optional string, identifying the enduser. It is necessary when doing any operation on a view.
        """
#    def __init__(self, appkey=None, api_server='localhost:9000', secrets_yaml=None):
        self.appkey = appkey
        self.enduser = enduser
        self.api_server = api_server
        if self.api_server.startswith("localhost"):
            self.base_url = "http://%s/empire/" % self.api_server
        else:
            self.base_url = "https://%s/empire/" % self.api_server
        self.stream_chunk_size = 128  # This is set low because lines aren't very long.
        if secrets_yaml:
            d = pyaml.yaml.load(open(secrets_yaml))
            self.service_secrets = {name: {o: v['value'] for o,v in d[name]['option'].items()} for name in d}
            # Convert all secrets to strings
            # TODO Remove these workarounds
            for s in self.service_secrets:
                if "scope" in self.service_secrets[s]:
                    del self.service_secrets[s]["scope"]
                for k in self.service_secrets[s]:
                    self.service_secrets[s][k] = str(self.service_secrets[s][k])
        else:
            self.service_secrets = None
        self.sessionkey = None

    def connect(self, service, secrets=None):
        url = self.base_url + 'services/%s/connect' % service
        if not secrets:
            if not self.service_secrets:
                raise ValueError("secrets must be provided on connect command, or secrets_yaml file must be given "
                                 "when constructing this instance")
            secrets = self.service_secrets[service]

            # TODO: Better err if self.service_secrets doesn't exist
        data = json.dumps(secrets)
        return self._do_request('post', url, data=data)

    def describe(self, service=None, table=None):
        url = self.base_url + "services"
        if service and table:
            url += '/%s/%s' % (service, table)
        elif service and not table:
            url += '/%s' % service
        elif not service and table:
            raise ValueError("Service must be specified if table is specified")

        return self._do_request('get', url)

    def print_query(self, sql):
        """
        Paginated printing of an SQL query
        """
        pager.page(self.query(sql, decode=False))

    def query(self, sql, decode=True):
        """
        Issue a SQL query, with an iterator over row results
        """
        url = self.base_url + "query"
        data = json.dumps({"query": sql})

        r = self._do_request('post', url, data=data, stream=True, intact=True)
        try:
            for l in r.iter_lines(chunk_size=self.stream_chunk_size):
                if decode:
                    yield json.loads(l)
                else:
                    yield l
        finally:
            if hasattr(r, 'connection'):
                r.connection.close()

    def insert(self, service, table, row):
        """
        Insert a new row into this service table.
        The row should be a dict of {column: value}
        """
        url = self.base_url + "services/%s/%s" % (service, table)
        data = json.dumps(row)
        return self._do_request('post', url, data=data)

    def materialize_view(self, name, sql):
        """
        Materialize a SQL query as a view. This creates or updates a view.
        """
        if not self.enduser:
            raise EmpireException("Cannot use materialized view within a session initiated without an enduser")
        url = self.base_url + "view/%s" % name
        data = json.dumps({"query": sql})
        return self._do_request('put', url, data=data)

    def drop_view(self, name):
        """
        Delete a materialized view of SQL query
        """
        if not self.enduser:
            raise EmpireException("Cannot use materialized view within a session initiated without an enduser")
        url = self.base_url + "view/%s" % name
        return self._do_request('delete', url)

    def view_ready(self, name):
        """
        Boolean check if a materialized view is ready for querying.
        @note The user is expected to check view_ready before calling query()
        """
        r = self._view_status(name)
        if r["viewStatus"] == "ready":
            return True
        elif r["viewStatus"] == "pending":
            return False
        else:
            raise EmpireException("Unknown view status: %s" % r["viewStatus"])

    def view_materialized_at(self, name):
        """
        Datetime that this view was materialized at. None if the
        materialization is currently pending.
        """
        r = self._view_status(name)
        if "materializedAt" in r:
            return dateutil.parser.parse(r["materializedAt"])
        else:
            return None

    def _view_status(self, name):
        if not self.enduser:
            raise EmpireException("Cannot use materialized view within a session initiated without an enduser")
        url = self.base_url + "view/%s/status" % name
        return self._do_request('get', url)

    def walkthrough(self):
        lastservice = None
        lasttable = None
        if self.service_secrets:
            for s in self.service_secrets:
                try:
                    print "empire.connect(%s)" % repr(s)
                    self.connect(s)
            
                    for t in self.describe(s)["service"]["tables"]:
                        t = t["table"]
                        # These mailchimp tables can only be queried
                        # when filtering by a particular list.
                        if s == "mailchimp":
                            skip_mc_tables = ["list_member", "campaign", "campaign_sent_to", "campaign_opened"]
                            if t in skip_mc_tables:
                                continue

                        sql = "SELECT * FROM %s.%s LIMIT 5" % (s, t)
                        # We print the repr so that strings are correctly quoted
                        print "empire.query(%s)" % repr(str(sql))
                        for row in self.query(sql):
                            print "    %s..." % repr(row)[:60]
                        lastservice, lasttable = s, t
                except Exception, e:
                    print "Error in service", s, e
            if self.enduser:
                print 'empire.materialize_view("view_name", "SELECT * FROM %s.%s LIMIT 5")' % (lastservice, lasttable)
                self.materialize_view("view_name", "SELECT * FROM %s.%s LIMIT 5" % (lastservice, lasttable))
                print 'while not empire.view_ready("view_name"):\n    time.sleep(0.1)'
                while not self.view_ready("view_name"):
                    time.sleep(0.01)
                print 'empire.query("SELECT * FROM view_name")'
                for row in self.query("SELECT * FROM view_name"):
                    print "    %s..." % repr(row)[:60]
                print 'empire.drop_view("view_name")'
                self.drop_view("view_name")
            else:
                print "Please specify an enduser parameter when instantiating the client, so that you can try materialized views"
        else:
            print "Please connect some services in https://login.empiredata.co, and download the new yaml file"

    def _do_request(self, *args, **kwargs):
        self._ensure_session()
        headers = {'Authorization': 'Empire sessionkey="%s"' % self.sessionkey}
        kwargs.setdefault('headers', {})
        # Does this overwrite the kwargs, in case the user wanted that dict later?
        kwargs['headers']['Authorization'] = 'Empire sessionkey="%s"' % self.sessionkey
        return self._do_request_help(*args, **kwargs)

    def _ensure_session(self):
        if not self.sessionkey:
            if self.enduser:
                # Manually construct the query parameter, because POST will
                # put it in the body by default
                url = self.base_url + 'session/create?enduser=%s' % urllib.quote(self.enduser)
            else:
                url = self.base_url + 'session/create'
            headers = {'Authorization': 'Empire appkey="%s"' % self.appkey}
            r = self._do_request_help('post', url, headers=headers)
            self.sessionkey = r["sessionkey"]
            #print >> sys.stderr, "Created session"

    def _do_request_help(self, *args, **kwargs):
        kwargs.setdefault('headers', {})

        # For POST requests with data, specify that they are JSON
        if 'data' in kwargs:
            kwargs['headers'].setdefault('content-type', 'application/json')

        kwargs.setdefault('stream', True)

        intact = kwargs.pop('intact', False)

        r = requests.request(*args, **kwargs)
        if intact:
            return r

        try:
            result = r.json()
            if result["status"] != "OK":
                raise EmpireException(result["error"])
            return result
        except ValueError, e:
            raise EmpireException(repr(e) + " " + r.text)
        finally:
            r.connection.close()
