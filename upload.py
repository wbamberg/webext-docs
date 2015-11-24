import sys
import os
import json
import requests

MDN_BASE_URL = "https://developer.allizom.org"

user = sys.argv[2]
passwd = sys.argv[3]

headers = {'Content-type': 'application/json'}

def upload(ns, name, head, data):
    if name == 'INDEX':
        url = MDN_BASE_URL + "/en-US/Add-ons/WebExtensions/API/" + ns
    else:
        url = MDN_BASE_URL + "/en-US/Add-ons/WebExtensions/API/" + ns + "/" + name

    j = json.loads(head)
    j['content'] = data
    content = json.dumps(j)

    print url
    r = requests.put(url, auth=(user, passwd), headers=headers, data=content)
    print r.status_code

def read_head(f):
    head = ''
    while True:
        line = f.readline()
        head += line
        if '}' in line:
            break
    return head

def upload_file(ns, name, fpath):
    f = open(fpath)
    head = read_head(f)
    data = f.read()
    upload(ns, name, head, data)
    f.close()

for ns in os.listdir(sys.argv[1]):
    path = os.path.join(sys.argv[1], ns)
    upload_file(ns, 'INDEX', os.path.join(path, 'INDEX'))

    for name in os.listdir(path):
        if name == 'INDEX': continue

        fpath = os.path.join(path, name)
        f = open(fpath)
        head = read_head(f)
        data = f.read()
        upload(ns, name, head, data)
