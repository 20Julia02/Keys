import requests
from requests_oauthlib import OAuth1
from ..config import CONSUMER_KEY, CONSUMER_SECRET

oauth = OAuth1(
    client_key=CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    signature_method='HMAC-SHA1',
    signature_type='auth_header'
)


def fetch_student_data_from_usos(fields='id|first_name|last_name|email|student_programmes|photo_urls'):
    url = 'https://apps.usos.pw.edu.pl/services/users/student_index'
    params = {
        'fields': fields,
        'format': 'json'
    }
    response = requests.get(url, auth=oauth, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None


def fetch_staff_data_from_usos(fields='id|first_name|last_name|email|employment_position|photo_urls'):
    url = 'https://apps.usos.pw.edu.pl/services/users/staff_index'
    params = {
        'fields': fields,
        'format': 'json'
    }
    response = requests.get(url, auth=oauth, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None
