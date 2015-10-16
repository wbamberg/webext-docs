# python json-transform.py data/ out windows tabs extension bookmarks cookies i18n browser_action context_menus runtime idle storage web_navigation web_request

# Needed docs (initial):
# - windows
# - tabs
# - extension
# - bookmarks
# - cookies
# - i18n
# - browserAction
# - contextMenus
# - runtime
# - idle
# - storage
# - webNavigation
# - webRequest

# - notifications (IDL)
# - alarms (IDL)

import sys
import json
import os.path

in_dir = sys.argv[1]
out_dir = sys.argv[2]

def generate(name):
    in_path = os.path.join(in_dir, name + '.json')
    text = open(in_path).read()
    lines = text.split('\n')
    lines = [ line for line in lines if not line.strip().startswith('//') ]
    text = '\n'.join(lines)

    data = json.loads(text)
    for ns in data:
        print '= Namespace {} ='.format(ns['namespace'])
        print

        for func in ns.get('functions', []):
            print '=== Function {} ==='.format(func['name'])
            print func.get('description', '<No description>')
            print
        print

        for prop in ns.get('properties', []):
            print '=== Property {} ==='.format(prop)
            print ns['properties'][prop]['description']
            print
        print

        for typ in ns.get('types', []):
            print '=== Type {} ==='.format(typ['id'])
            print 'Type <b>{}</b>'.format(typ['type'])
            print typ.get('description', '')

            if 'enum' in typ:
                def fmt_enum(e):
                    if type(e) == dict:
                        return e['name']
                    else:
                        return e

                print 'Enumeration {}'.format(', '.join([ fmt_enum(e) for e in typ['enum'] ]))
            print
        print

        for event in ns.get('events', []):
            print '=== Event {} ==='.format(event['name'])
            print event.get('description', '')
            print
        print

for name in sys.argv[3:]:
    generate(name)

