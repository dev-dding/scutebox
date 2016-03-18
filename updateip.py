import requests
url = 'http://192.168.0.249/updatescuteip.php'
payload = {'key': 'value1', 'scuteid': 'AbcdeEDFGI', 'scuteip':'192.168.99.126'}

# GET with params in URL
r = requests.get(url, params=payload)

# Response, status etc
print r.text
print r.status_code
