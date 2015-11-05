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

LINK1 = 'https://chromium.googlesource.com/chromium/src/+/master/chrome/common/extensions/api/'
LINK2 = 'https://chromium.googlesource.com/chromium/src/+/master/extensions/common/api/'

JSON_SOURCES = {
    'windows': LINK1,
    'tabs': LINK1,
    'extension': LINK1,
    'bookmarks': LINK1,
    'cookies': LINK1,
    'i18n': LINK1,
    'browser_action': LINK1,
    'context_menus': LINK1,
    'runtime': LINK2,
    'idle': LINK2,
    'storage': LINK2,
    'web_navigation': LINK1,
    'web_request': LINK2,
}

CHROMIUM_DOCS = 'https://developer.chrome.com/extensions/'

LICENSE = '''
// Copyright 2015 The Chromium Authors. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
//
//    * Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
//    * Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
//    * Neither the name of Google Inc. nor the names of its
// contributors may be used to endorse or promote products derived from
// this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

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

def generate_compatibility(out, json_name, ns, anchor = None):
    print >>out, '<h2 id="Compatibility">Compatibility</h2>'

    chromium_api = 'chrome.' + ns

    chromium_docs = CHROMIUM_DOCS + ns
    if anchor:
        chromium_docs += '#' + anchor

    chromium_json = JSON_SOURCES[json_name] + json_name + '.json'

    print >>out, "This API is based on Chromium's <a href=\"{}\"><code>{}</code></a> API.".format(chromium_docs, chromium_api)
    print >>out, 'This documentation is derived from <a href="{}"><code>{}.json</code></a> in the Chromium code.'.format(chromium_json, json_name)

    print >>out, '<div class="hidden"><pre>'
    print >>out, LICENSE.strip()
    print >>out, '</pre></div>'

def generate_function(json_name, ns, func):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + func['name']
    out = open(os.path.join(out_dir, slug), 'w')

    title = ns['namespace'] + '.' + func['name'] + '()'
    print >>out, '{{ "title": "{}", "show_toc": 0 }}'.format(title)

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

    generate_compatibility(out, json_name, ns['namespace'], 'method-' + func['name'])

    out.close()

def generate_type(json_name, ns, t):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + t['id']
    out = open(os.path.join(out_dir, slug), 'w')

    title = ns['namespace'] + '.' + t['id']
    print >>out, '{{ "title": "{}", "show_toc": 0 }}'.format(title)

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

    generate_compatibility(out, json_name, ns['namespace'], 'type-' + t['id'])

    out.close()

def generate_property(json_name, ns, name, prop):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + name
    out = open(os.path.join(out_dir, slug), 'w')

    title = ns['namespace'] + '.' + name
    print >>out, '{{ "title": "{}", "show_toc": 0 }}'.format(title)

    print >>out, '<p>{}</p>'.format(prop.get('description', name))

    generate_compatibility(out, json_name, ns['namespace'], 'property-' + name)

    out.close()

# FIXME: Need to add extra parameters.
def generate_event(json_name, ns, func):
    #print '<p>{{ WebExtRef("{}") }}</p>'.format(ns.name)

    os.system('mkdir -p {}'.format(os.path.join(out_dir, ns['namespace'])))
    slug = ns['namespace'] + '/' + func['name']
    out = open(os.path.join(out_dir, slug), 'w')

    title = ns['namespace'] + '.' + func['name']
    print >>out, '{{ "title": "{}", "show_toc": 0 }}'.format(title)

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

    generate_compatibility(out, json_name, ns['namespace'], 'event-' + func['name'])

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
            generate_function(name, ns, func)

        for prop in ns.get('properties', []):
            generate_property(name, ns, prop, ns['properties'][prop])

        for typ in ns.get('types', []):
            generate_type(name, ns, typ)

        for event in ns.get('events', []):
            generate_event(name, ns, event)

        index_file = ns['namespace'] + '/' + 'INDEX'
        out = open(os.path.join(out_dir, index_file), 'w')

        title = ns['namespace']
        print >>out, '{{ "title": "{}", "show_toc": 0 }}'.format(title)

        print >>out, '<p>{}</p>'.format(ns.get('description', ns['namespace']))

        if 'types' in ns:
            print >>out, '<h2 id="Types">Types</h2>'
            print >>out, '<dl>'
            for t in ns.get('types', []):
                print >>out, '<dt><code>{}</code></dt>'.format(t['id'])
                if 'description' in t:
                    print >>out, '<dd>{}</dd>'.format(t['description'])
            print >>out, '</dl>'

        if 'properties' in ns:
            print >>out, '<h2 id="Properties">Properties</h2>'
            print >>out, '<dl>'
            for prop in ns.get('properties', []):
                print >>out, '<dt><code>{}</code></dt>'.format(prop)
                if 'description' in ns['properties'][prop]:
                    print >>out, '<dd>{}</dd>'.format(ns['properties'][prop]['description'])
            print >>out, '</dl>'

        if 'functions' in ns:
            print >>out, '<h2 id="Functions">Functions</h2>'
            print >>out, '<dl>'
            for func in ns.get('functions', []):
                args = ', '.join([ p['name'] for p in func['parameters'] ])
                print >>out, '<dt><code>{}({})</code></dt>'.format(func['name'], args)
                if 'description' in func:
                    print >>out, '<dd>{}</dd>'.format(func['description'])
            print >>out, '</dl>'

        if 'events' in ns:
            print >>out, '<h2 id="Events">Events</h2>'
            print >>out, '<dl>'
            for func in ns.get('events', []):
                args = ', '.join([ p['name'] for p in func.get('parameters', []) ])
                print >>out, '<dt><code>{}({})</code></dt>'.format(func['name'], args)
                if 'description' in func:
                    print >>out, '<dd>{}</dd>'.format(func['description'])
            print >>out, '</dl>'

        generate_compatibility(out, name, ns['namespace'])

        out.close()

for name in sys.argv[3:]:
    generate(name)

