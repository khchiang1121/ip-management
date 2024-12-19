import requests
import pytest

API_URL = "http://127.0.0.1:8100"

@pytest.mark.parametrize("server_id,status_code,message", [
    ("test2", 200, {"message": "Server deleted"}),
    ("test2", 404, {"error": "Server not found"})
])
def test_delete_server(server_id, status_code, message):
    url = API_URL + '/api/servers/' + server_id
    response = requests.delete(url)
    assert response.status_code == status_code
    assert response.json() == message








