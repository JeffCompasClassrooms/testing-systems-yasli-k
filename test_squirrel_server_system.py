import pytest
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.parse
import sqlite3
from squirrel_db import SquirrelDB


@pytest.fixture(autouse=True)
def setup_and_cleanup_database():
    # Simulate squirrel_db.db.template by creating an empty squirrels table
    db_file = "squirrel_db.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE squirrels (id INTEGER PRIMARY KEY, name TEXT, size TEXT)")
    conn.commit()
    conn.close()
    yield
    # Clean up
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(autouse=True, scope='session')
def start_and_stop_server():
    # Start the server
    proc = subprocess.Popen([sys.executable, 'squirrel_server.py'])
    time.sleep(0.5)  # Wait for server to start
    yield
    # Stop the server
    proc.terminate()
    proc.wait()


@pytest.fixture
def http_client():
    conn = http.client.HTTPConnection('localhost:8080')
    yield conn
    conn.close()


@pytest.fixture
def request_body():
    return urllib.parse.urlencode({'name': 'Sam', 'size': 'large'})


@pytest.fixture
def request_headers():
    return {'Content-Type': 'application/x-www-form-urlencoded'}


@pytest.fixture
def db():
    return SquirrelDB()


@pytest.fixture
def make_a_squirrel(db):
    db.createSquirrel("Fred", "small")


def describe_squirrel_server_api():
    def describe_get_squirrels():
        def it_returns_200_status_code(http_client):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            assert response.status == 200

        def it_returns_json_content_type_header(http_client):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            assert response.getheader('Content-Type') == "application/json"

        def it_returns_empty_json_array(http_client):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            response_body = response.read()
            assert json.loads(response_body) == []

        def it_returns_json_array_with_one_squirrel(http_client, make_a_squirrel):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            response_body = response.read()
            squirrels = json.loads(response_body)
            assert len(squirrels) == 1
            assert squirrels[0] == {"id": 1, "name": "Fred", "size": "small"}

        def it_returns_json_array_with_multiple_squirrels(http_client, db):
            db.createSquirrel("Fred", "small")
            db.createSquirrel("Sam", "large")
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            response_body = response.read()
            squirrels = json.loads(response_body)
            assert len(squirrels) == 2
            assert squirrels == [
                {"id": 1, "name": "Fred", "size": "small"},
                {"id": 2, "name": "Sam", "size": "large"}
            ]

    def describe_get_squirrel_by_id():
        def it_returns_squirrel_if_exists(http_client, make_a_squirrel):
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            response_body = json.loads(response.read())
            assert response.status == 200
            assert response.getheader('Content-Type') == "application/json"
            assert response_body == {"id": 1, "name": "Fred", "size": "small"}

        def it_returns_404_for_non_existing_id(http_client):
            http_client.request("GET", "/squirrels/999")
            response = http_client.getresponse()
            assert response.status == 404
            assert response.getheader('Content-Type') == "text/plain"
            assert response.read().decode('utf-8') == "404 Not Found"

    def describe_post_squirrels():
        def it_creates_squirrel_and_returns_201(http_client, request_headers, request_body, db):
            http_client.request("POST", "/squirrels", body=request_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 201
            # Verify database side effect
            squirrels = db.getSquirrels()
            assert len(squirrels) == 1
            assert squirrels[0] == {"id": 1, "name": "Sam", "size": "large"}

        # def it_fails_with_crash_for_missing_data(http_client, request_headers, db):
        #     empty_body = urllib.parse.urlencode({})
        #     http_client.request("POST", "/squirrels", body=empty_body, headers=request_headers)
        #     with pytest.raises(http.client.RemoteDisconnected):
        #         http_client.getresponse()
        #     # Verify no database changes
        #     assert len(db.getSquirrels()) == 0

    def describe_put_squirrels():
        def it_updates_existing_squirrel(http_client, request_headers, make_a_squirrel, db):
            update_body = urllib.parse.urlencode({'name': 'Nutty', 'size': 'medium'})
            http_client.request("PUT", "/squirrels/1", body=update_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 204
            # Verify database side effect
            squirrel = db.getSquirrel("1")
            assert squirrel == {"id": 1, "name": "Nutty", "size": "medium"}

        def it_returns_404_for_non_existing_id(http_client, request_headers):
            body = urllib.parse.urlencode({'name': 'Nutty', 'size': 'medium'})
            http_client.request("PUT", "/squirrels/999", body=body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        # def it_fails_with_crash_for_missing_data(http_client, request_headers, make_a_squirrel, db):
        #     empty_body = urllib.parse.urlencode({})
        #     http_client.request("PUT", "/squirrels/1", body=empty_body, headers=request_headers)
        #     with pytest.raises(http.client.RemoteDisconnected):
        #         http_client.getresponse()
        #     # Verify no database changes
        #     squirrel = db.getSquirrel("1")
        #     assert squirrel == {"id": 1, "name": "Fred", "size": "small"}

    def describe_delete_squirrels():
        def it_deletes_existing_squirrel(http_client, make_a_squirrel, db):
            http_client.request("DELETE", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 204
            # Verify database side effect
            squirrel = db.getSquirrel("1")
            assert squirrel is None

        def it_returns_404_for_non_existing_id(http_client):
            http_client.request("DELETE", "/squirrels/999")
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

    def describe_404_failure_conditions():
        def it_returns_404_for_unknown_path(http_client):
            http_client.request("GET", "/unknown")
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_post_with_id(http_client, request_headers, request_body):
            http_client.request("POST", "/squirrels/1", body=request_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_put_without_id(http_client, request_headers, request_body):
            http_client.request("PUT", "/squirrels", body=request_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_delete_without_id(http_client):
            http_client.request("DELETE", "/squirrels")
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_get_nested_path(http_client):
            http_client.request("GET", "/squirrels/1/extra")
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_post_nested_path(http_client, request_headers, request_body):
            http_client.request("POST", "/squirrels/1/extra", body=request_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_put_nested_path(http_client, request_headers, request_body):
            http_client.request("PUT", "/squirrels/1/extra", body=request_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

        def it_returns_404_for_delete_nested_path(http_client):
            http_client.request("DELETE", "/squirrels/1/extra")
            response = http_client.getresponse()
            assert response.status == 404
            assert response.read().decode('utf-8') == "404 Not Found"

    def describe_501_failure_conditions():
        def it_returns_501_for_invalid_method_get(http_client):
            http_client.request("PATCH", "/squirrels")
            response = http_client.getresponse()
            assert response.status == 501
            assert "Unsupported method" in response.read().decode('utf-8')

        def it_returns_501_for_invalid_method_id(http_client):
            http_client.request("PATCH", "/squirrels/1")
            response = http_client.getresponse()
            assert response.status == 501
            assert "Unsupported method" in response.read().decode('utf-8')
    

    def describe_bad_request_400():
        def it_returns_400_when_creating_with_missing_size(http_client, request_headers, db):
            bad_body = urllib.parse.urlencode({'name': 'Fluffy'})  # missing size
            http_client.request("POST", "/squirrels", body=bad_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 400
            assert response.getheader('Content-Type') == "text/plain"
            body = response.read().decode('utf-8')
            assert "Bad Request" in body
            # Database unchanged
            assert len(db.getSquirrels()) == 0

        def it_returns_400_when_creating_with_missing_name(http_client, request_headers, db):
            bad_body = urllib.parse.urlencode({'size': 'large'})  # missing name
            http_client.request("POST", "/squirrels", body=bad_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 400
            assert "Bad Request" in response.read().decode('utf-8')
            assert len(db.getSquirrels()) == 0

        def it_returns_400_when_updating_with_missing_size(http_client, request_headers, make_a_squirrel, db):
            bad_body = urllib.parse.urlencode({'name': 'Nutty'})  # missing size
            http_client.request("PUT", "/squirrels/1", body=bad_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 400
            assert "Bad Request" in response.read().decode('utf-8')
            # Verify original data unchanged
            squirrel = db.getSquirrel("1")
            assert squirrel["name"] == "Fred"

        def it_returns_400_when_updating_with_missing_name(http_client, request_headers, make_a_squirrel, db):
            bad_body = urllib.parse.urlencode({'size': 'medium'})  # missing name
            http_client.request("PUT", "/squirrels/1", body=bad_body, headers=request_headers)
            response = http_client.getresponse()
            assert response.status == 400
            squirrel = db.getSquirrel("1")
            assert squirrel["name"] == "Fred"  # unchanged