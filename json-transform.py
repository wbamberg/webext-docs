# Run as:
# python json-transform.py data/ out windows tabs extension bookmarks \
#   cookies i18n browser_action context_menus runtime idle storage web_navigation web_request
# Output is generated in out/<namespace>/<event/function/property/type>

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

import os
import sys
import json
import os.path
import collections

in_dir = sys.argv[1]
out_dir = sys.argv[2]

def describe_type(t):
    def simple_describe(t):
        if 'type' in t:
            if t['type'] == 'array':
                return simple_describe(t['items']) + ' array'
            else:
                return t['type']
        elif 'choices' in t:
            return ' or '.join([ simple_describe(t2) for t2 in t['choices'] ])
        elif '$ref' in t:
            return t['$ref']
        else:
            print 'UNKNOWN', t
            raise 'BAD'

    base = simple_describe(t)
    if t.get('optional', False):
        return 'optional {}'.format(base)
    else:
        return base

def function_example(param):
    if 'parameters' in param:
        fparams = ', '.join([ p['name'] for p in param['parameters'] ])
    else:
        fparams = ''
    return 'function({}) {{...}}'.format(fparams)

def describe_param(param):
    if param.get('type') == 'function':
        return (function_example(param), describe_type(param))
    else:
        return (param['name'], describe_type(param))

def describe_object(obj):
    props = obj.get('properties')
    if not props:
        return ''

    desc = ''
    desc += '<table class="standard-table"><tbody>\n'

    for prop in props:
        desc += '  <tr>\n'
        desc += '    <td>{}</td>\n'.format(describe_type(props[prop]))
        desc += '    <td><code><b>{}</b></code></td>\n'.format(prop)
        desc += '    <td>{}</td>\n'.format(props[prop].get('description', ''))
        desc += '  </td>\n'

    desc += '</tbody></table>\n'

    return desc

def describe_enum(enum):
    if len([ True for x in enum if type(x) != unicode ]):
        desc = 'Possible values are:'
        desc += '<table class="standard-table"><tbody>\n'

        for e in enum:
            desc += '  <tr>\n'
            desc += '    <td><code><b>{}</b></code></td>\n'.format(e['name'])
            desc += '    <td>{}</td>\n'.format(e['description'])
            desc += '  </td>\n'

        desc += '</tbody></table>\n'
        return desc
    else:
        return 'Possible values are: {}'.format(', '.join([ '<code>"' + s + '"</code>' for s in enum ]))

def describe_function(func):
    if 'parameters' not in func:
        return ''

    desc = ''
    desc += '<code>{}</code>\n'.format(function_example(func))
    desc += '<table class="standard-table"><tbody>\n'

    for param in func['parameters']:
        desc += '  <tr>\n'
        desc += '    <td>{}</td>\n'.format(describe_type(param))
        desc += '    <td><code><b>{}</b></code></td>\n'.format(param['name'])
        if 'description' in param:
            desc += '    <td>{}</td>\n'.format(param['description'])
        desc += '  </td>\n'

    desc += '</tbody></table>\n'

    return desc

def generate_function(ns, func):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + func['name']
    out = open(os.path.join(out_dir, slug), 'w')

    print >>out, '<p>{}</p>'.format(func.get('description', func['name']))

    print >>out, '<h2 id="Syntax">Syntax</h2>'

    print >>out, '<pre class="brush: js">'
    print >>out, 'browser.{}.{}('.format(ns['namespace'], func['name'])

    info = []
    for (i, param) in enumerate(func['parameters']):
        (name, desc) = describe_param(param)
        if i != len(func['parameters']) - 1:
            name += ','
        info.append((name, desc))

    if info:
        pad = max([ len(name) for (name, desc) in info ])
    else:
        pad = 0
    for (name, desc) in info:
        print >>out, '  {:<{}} // {}'.format(name, pad, desc)
    print >>out, ')'
    print >>out, '</pre>'

    print >>out, '<h3 id="Parameters">Parameters</h3>'
    print >>out, '<dl>'
    for param in func['parameters']:
        print >>out, '<dt><code>{}</code> ({})</dt>'.format(param['name'], describe_type(param))

        desc = param.get('description', '')

        if param.get('type') == 'object':
            desc += describe_object(param)
        elif param.get('type') == 'function':
            desc += describe_function(param)
        if desc:
            print >>out, '<dd>{}</dd>'.format(desc)

    print >>out, '</dl>'

    if 'returns' in func and 'description' in func['returns']:
        print >>out, '<h3 id="Returns">Returns</h3>'
        print >>out, '<p>{}</p>'.format(func['returns']['description'])

    out.close()

def generate_type(ns, t):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + t['id']
    out = open(os.path.join(out_dir, slug), 'w')

    print >>out, '<p>{}</p>'.format(t.get('description', t['id']))

    print >>out, '<h2 id="Type">Type</h2>'

    if t['type'] == 'object':
        print >>out, '<p>Values of this type are objects.</p>'
        print >>out, describe_object(t)
    elif t['type'] == 'string':
        print >>out, '<p>Values of this type are strings.'
        if 'enum' in t:
            print >>out, describe_enum(t['enum'])
        print >>out, '</p>'

    elif t['type'] == 'array':
        print >>out, '<p>Values of this type are {}s.'.format(describe_type(t))
        if 'minItems' in t:
            assert t['minItems'] == t['maxItems']
            print >>out, 'The array should contain {} elements.'.format(t['minItems'])

        items = t['items']
        if 'minimum' in items:
            print >>out, 'Array elements should be between {} and {}.'.format(
                t['items']['minimum'], t['items']['maximum'])
        print >>out, '</p>'

        if items['type'] == 'object':
            print >>out, '<p>Elements of the array look like:</p>'
            print >>out, describe_object(items)
    else:
        print t
        raise 'UNKNOWN'

    out.close()

def generate_property(ns, name, prop):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + name
    out = open(os.path.join(out_dir, slug), 'w')

    print >>out, '<p>{}</p>'.format(prop.get('description', name))

    out.close()

def generate_event(ns, func):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + func['name']
    out = open(os.path.join(out_dir, slug), 'w')

    print >>out, '<p>{}</p>'.format(func.get('description', func['name']))

    print >>out, '<h2 id="Syntax">Syntax</h2>'

    params = func.get('parameters', [])

    print >>out, '<pre class="brush: js">'
    if len(params):
        print >>out, 'browser.{}.{}.addListener(function('.format(ns['namespace'], func['name'])

        info = []
        for (i, param) in enumerate(params):
            (name, desc) = describe_param(param)
            if i != len(func['parameters']) - 1:
                name += ','
            info.append((name, desc))

        if info:
            pad = max([ len(name) for (name, desc) in info ])
        else:
            pad = 0
        for (name, desc) in info:
            print >>out, '  {:<{}} // {}'.format(name, pad, desc)
        print >>out, ') {...})'
    else:
        print >>out, 'browser.{}.{}.addListener(function() {{...}})'.format(ns['namespace'], func['name'])

    print >>out, 'browser.{}.{}.removeListener(listener)'.format(ns['namespace'], func['name'])
    print >>out, 'browser.{}.{}.hasListener(listener)'.format(ns['namespace'], func['name'])
    print >>out, '</pre>'

    print >>out, '<h3 id="Parameters">Listener parameters</h3>'
    print >>out, '<dl>'
    for param in params:
        print >>out, '<dt><code>{}</code> ({})</dt>'.format(param['name'], describe_type(param))

        desc = param.get('description', '')

        if param.get('type') == 'object':
            desc += describe_object(param)
        elif param.get('type') == 'function':
            desc += describe_function(param)
        if desc:
            print >>out, '<dd>{}</dd>'.format(desc)

    print >>out, '</dl>'

    if 'returns' in func and 'description' in func['returns']:
        print >>out, '<h3 id="Returns">Returns</h3>'
        print >>out, '<p>{}</p>'.format(func['returns']['description'])

    out.close()

# We want to preserve the order from the original JSON file.
def json_hook(pairs):
    return collections.OrderedDict(pairs)

def generate(name):
    in_path = os.path.join(in_dir, name + '.json')
    text = open(in_path).read()
    lines = text.split('\n')
    lines = [ line for line in lines if not line.strip().startswith('//') ]
    text = '\n'.join(lines)

    data = json.loads(text, object_pairs_hook=json_hook)
    for ns in data:
        for func in ns.get('functions', []):
            generate_function(ns, func)

        for prop in ns.get('properties', []):
            generate_property(ns, prop, ns['properties'][prop])

        for typ in ns.get('types', []):
            generate_type(ns, typ)

        for event in ns.get('events', []):
            generate_event(ns, event)

for name in sys.argv[3:]:
    generate(name)

