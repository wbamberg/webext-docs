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
import re

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
    'extension_types': LINK2
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

COMPAT_TABLE = '''
<h2 id="Browser_compatibility">Browser compatibility</h2>
<p>{{ CompatibilityTable() }}</p>
<div id="compat-desktop">
<table class="compat-table">
 <tbody>
  <tr>
   <th>Feature</th>
   <th>Chrome</th>
   <th>Edge</th>
   <th>Firefox (Gecko)</th>
   <th>Opera</th>
  </tr>
  <tr>
   <td>Basic support</td>
   <td>{{ CompatChrome('46') }}</td>
   <td>{{ CompatUnknown() }}</td>
   <td>{{ %s }}</td>
   <td>{{ CompatOpera('33') }}</td>
  </tr>
 </tbody>
</table>
</div>
<div id="compat-mobile">
<table class="compat-table">
 <tbody>
  <tr>
   <th>Feature</th>
   <th>Edge</th>
   <th>Firefox OS</th>
   <th>Firefox Mobile (Gecko)</th>
  <tr>
   <td>Basic support</td>
   <td>{{ CompatNo() }}</td>
   <td>{{ CompatNo() }}</td>
   <td>{{ CompatNo() }}</td>
  </tr>
 </tbody>
</table>
</div>
'''

in_dir = sys.argv[1]
out_dir = sys.argv[2]

def get_common_tags(out, namespace):
    common_tags = '"API", "Reference", "WebExtensions", "Add-ons", "Extensions", "Non-standard", '
    common_tags += '"{}", '.format(namespace)
    return common_tags

def get_api_tags(out, namespace):
    tags = '"tags": ['
    tags += get_common_tags(out, namespace)
    tags += '"{}"]'.format("Interface")
    return tags

def get_api_component_tags(out, namespace, name, component_type):
    tags = '"tags": ['
    tags += get_common_tags(out, namespace)
    tags += '"{}", '.format(name)
    tags += '"{}"] '.format(component_type)
    return tags

def collect_anonymous_objects(ns, obj, anonymous_objects):
    props = obj.get('properties')
    if not props:
        return
    for prop_name in props:
        prop = props[prop_name]
        if 'type' in prop and prop['type'] == 'object' and 'properties' in prop:
            anonymous_objects[prop_name] = prop
            collect_anonymous_objects(ns, prop, anonymous_objects)

def describe_anonymous_objects(ns, anonymous_objects, out):
    if len(anonymous_objects) == 0:
        return
    print >>out, '<h2>Anonymous objects</h2>'
    for anon in anonymous_objects:
        anon_object = anonymous_objects.get(anon)
        if 'properties' in anon_object:
            print >>out, '<h3>{}</h3>'.format(anon)
            print >>out, '<p>{}</p>'.format(anon_object.get('description'))
            print >>out, describe_object(ns, anon_object)
            
def describe_type_as_text(t):
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

def describe_type(ns, t, name = None):
    if 'type' in t:
        if t['type'] == 'array':
            return '<code>array</code> of <code>{}</code>'.format(describe_type(ns, t['items']))
        elif name and t['type'] == 'object' and 'properties' in t:
            return '<a href="#{}"><code>{}</code></a>'.format(name, t['type'])
        else:
            return '<code>{}</code>'.format(t['type'])
    elif 'choices' in t:
        return ' or '.join([ '<code>{}</code>'.format(describe_type(ns, t2)) for t2 in t['choices'] ])
    elif '$ref' in t:
        ref = t['$ref']
        ref_components = ref.split(".")
        if len(ref_components) == 1:
            return "{{{{WebExtAPIRef('{}')}}}}".format(ns['namespace'] + "." + ref)
        else:
            return "{{{{WebExtAPIRef('{}')}}}}".format(ref)
    else:
        print 'UNKNOWN', t
        raise 'BAD'

def function_example(param):
    if 'parameters' in param:
        fparams = ', '.join([ p['name'] for p in param['parameters'] ])
    else:
        fparams = ''
    return 'function({}) {{...}}'.format(fparams)

def describe_param(ns, param):
    param_type = describe_type_as_text(param)
    if param.get('type') == 'function':
        return (function_example(param), param_type)
    else:
        return (param['name'], param_type)

def describe_object(ns, obj, anchor=False):
    props = obj.get('properties')
    if not props:
        return ''

    desc = ''
    desc += '''
    <table class="standard-table">
      <thead>
        <tr>
          <th scope="col" style="width: 20%;">Name</th>
          <th scope="col" colspan="2" rowspan="1">Type</th>
          <th scope="col" style="width: 50%;">Description</th>
        </tr>
      </thead>
      <tbody>\n
    '''
    for prop in props:
        desc += '  <tr>\n'
        # Name
        if anchor:
            desc += '    <td><code><a name="{}">{}</a></code></td>\n'.format(prop, prop)
        else:
            desc += '    <td><code>{}</code></td>\n'.format(prop)
        # Type
        if props[prop].get('optional'):
            desc += '    <td>{}</td>\n'.format(describe_type(ns, props[prop], prop))
            desc += '    <td>Optional</td>\n'
        else:
            desc += '    <td colspan="2" rowspan="1">{}</td>\n'.format(describe_type(ns, props[prop], prop))
        desc += '    <td>{}</td>\n'.format(props[prop].get('description', ''))
        desc += '  </tr>\n'

    desc += '</tbody></table>\n'

    return desc

def describe_enum(enum):
    if len([ True for x in enum if type(x) != unicode ]):
        desc = 'Possible values are:'
        desc += '<table class="standard-table"><tbody>\n'

        for e in enum:
            desc += '  <tr>\n'
            desc += '    <td><code>{}</code></td>\n'.format(e['name'])
            desc += '    <td>{}</td>\n'.format(e['description'])
            desc += '  </td>\n'

        desc += '</tbody></table>\n'
        return desc
    else:
        return 'Possible values are: {}.'.format(', '.join([ '<code>"' + s + '"</code>' for s in enum ]))

def describe_function(ns, func):
    if 'parameters' not in func or len(func['parameters']) == 0:
        return ''

    desc = ' The function is passed the following arguments:'
    desc += '''
    <table class="standard-table">
      <thead>
        <tr>
          <th scope="col" style="width: 20%;">Name</th>
          <th scope="col" colspan="2" rowspan="1">Type</th>
          <th scope="col" style="width: 50%;">Description</th>
        </tr>
      </thead>
      <tbody>\n
    '''
 
    for param in func['parameters']:
        desc += '  <tr>\n'
        desc += '    <td><code>{}</code></td>\n'.format(param['name'])

        if param.get('optional'):
            desc += '    <td>{}</td>\n'.format(describe_type(ns, param, param['name']))
            desc += '    <td>Optional</td>\n'
        else:
            desc += '    <td colspan="2" rowspan="1">{}</td>\n'.format(describe_type(ns, param, param['name']))
        desc += '    <td>{}</td>\n'.format(param.get('description', ''))
        desc += '  </tr>\n'

    desc += '</tbody></table>\n'

    return desc

def generate_preamble(namespace, name, kind):
    os.system('mkdir -p {}'.format(os.path.join(out_dir, namespace)))
    slug = namespace + '/' + name
    out = open(os.path.join(out_dir, slug), 'w')

    title = namespace + '.' + name
    if kind == 'Method':
        title += '()'

    print >>out, '{'
    print >>out, '"title": "{}",'.format(title)
    print >>out, '"show_toc": 0,'
    print >>out, get_api_component_tags(out, namespace, name, kind)
    print >>out, "}"

    print >>out, '{{AddonSidebar()}}'
    
    return out

def generate_postamble(namespace, name, obj, kind, json_name, out):
    ff_support = "CompatGeckoDesktop('45.0')"
    if obj.get('unsupported', False):
        ff_support = "CompatNo()"
    print >>out, COMPAT_TABLE%(ff_support)
    print >>out, '{{WebExtExamples}}'
    generate_acknowledgement(out, json_name, namespace, kind + name)

def generate_acknowledgement(out, json_name, ns, anchor = None):
    print >>out, '<div class="note">'
    print >>out, '<strong>Acknowledgements</strong>'

    chromium_api = 'chrome.' + ns

    chromium_docs = CHROMIUM_DOCS + ns
    if anchor:
        chromium_docs += '#' + anchor

    chromium_json = JSON_SOURCES[json_name] + json_name + '.json'

    print >>out, "<p>This API is based on Chromium's <a href=\"{}\"><code>{}</code></a> API. ".format(chromium_docs, chromium_api)
    print >>out, 'This documentation is derived from <a href="{}"><code>{}.json</code></a> in the Chromium code.</p>'.format(chromium_json, json_name)

    print >>out, "</div>"

    print >>out, '<div class="hidden"><pre>'
    print >>out, LICENSE.strip()
    print >>out, '</pre></div>'

def generate_function(json_name, ns, func):
    out = generate_preamble(ns['namespace'], func['name'], "Method")

    print >>out, '<p>{}</p>'.format(func.get('description', func['name']))

    print >>out, '<h2 id="Syntax">Syntax</h2>'

    print >>out, '<pre class="brush: js">'
    print >>out, 'browser.{}.{}('.format(ns['namespace'], func['name'])

    info = []
    for (i, param) in enumerate(func['parameters']):
        (name, desc) = describe_param(ns, param)
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
    
    anonymous_objects = {}

    for param in func['parameters']:
        if param.get('optional', False):
            print >>out, '<dt><code>{}</code>{{{{optional_inline}}}}</dt>'.format(param['name'])
        else:
            print >>out, '<dt><code>{}</code></dt>'.format(param['name'])

        desc = '{}. '.format(describe_type(ns, param))
        desc += param.get('description', '')

        if param.get('type') == 'object':
            desc += describe_object(ns, param)
            collect_anonymous_objects(ns, param, anonymous_objects)

        elif param.get('type') == 'function':
            desc += describe_function(ns, param)
        if desc:
            print >>out, '<dd>{}</dd>'.format(desc)

    print >>out, '</dl>'

    if 'returns' in func and 'description' in func['returns']:
        print >>out, '<h3>Return value</h3>'
        print >>out, '<p>{}. '.format(describe_type(ns, func['returns']))
        print >>out, '{}</p>'.format(func['returns']['description'])

    describe_anonymous_objects(ns, anonymous_objects, out)

    generate_postamble(ns['namespace'], func['name'], func, 'method-', json_name, out)

    out.close()

def generate_type(json_name, ns, t):
    out = generate_preamble(ns['namespace'], t['id'], "Type")

    print >>out, '<p>{}</p>'.format(t.get('description', t['id']))

    print >>out, '<h2 id="Type">Type</h2>'

    anonymous_objects = {}

    if t['type'] == 'object':
        print >>out, '<p>Values of this type are objects.</p>'
        print >>out, describe_object(ns, t, True)
        collect_anonymous_objects(ns, t, anonymous_objects)
    elif t['type'] == 'string':
        print >>out, '<p>Values of this type are strings.'
        if 'enum' in t:
            print >>out, describe_enum(t['enum'])
        print >>out, '</p>'

    elif t['type'] == 'array':
        print >>out, '<p>Values of this type are {}s.'.format(describe_type(ns, t))
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
            print >>out, describe_object(ns, items)
    else:
        print t
        raise 'UNKNOWN'

    describe_anonymous_objects(ns, anonymous_objects, out)

    generate_postamble(ns['namespace'], t['id'], t, 'type-', json_name, out)

    out.close()

def generate_property(json_name, ns, name, prop):
    out = generate_preamble(ns['namespace'], name, "Property")

    print >>out, '<p>{}</p>'.format(prop.get('description', name))

    generate_postamble(ns['namespace'], name, prop, 'property-', json_name, out)

    out.close()

def generate_event(json_name, ns, func):
    out = generate_preamble(ns['namespace'], func['name'], "Event")

    print >>out, '<p>{}</p>'.format(func.get('description', func['name']))

    print >>out, '<h2 id="Syntax">Syntax</h2>'

    params = func.get('parameters', [])

    print >>out, '<pre class="brush: js">'
    if len(params):
        print >>out, 'browser.{}.{}.addListener(function('.format(ns['namespace'], func['name'])

        info = []
        for (i, param) in enumerate(params):
            (name, desc) = describe_param(ns, param)
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
    
    extra_params = func.get('extraParameters', [])
    add_listener_params = ", ".join(["callback"] + [extra_param['name'] for extra_param in extra_params])
    
    print >>out, '<h3>addListener({})</h3>'.format(add_listener_params)
    print >>out, '<p>Adds a listener to this event.</p>'
    print >>out, '<h4>Parameters</h4>'
    print >>out, '<dl>'
    print >>out, '<dt><code>callback</code></dt>'
    
    callback_desc = "<p>Function that will be called when this event occurs."
    anonymous_objects = {}

    if len(params) > 0:
        callback_desc += " The function will be passed the following arguments:</p>"
        
        for param in params:
            param_name = param['name']
            if param_name == "details":
                callback_desc += '<dl><dt><code>details</code></dt><dd><p>An object providing details about the event. This object has the following structure:</p>'
            else:
                callback_desc += '<dl><dt><code>{}</code></dt>'.format(param['name'])
                callback_desc += '<dd>{}. {}'.format(describe_type(ns, param, param['name']), param.get('description', ''))

            if param.get('type') == 'object':
                callback_desc += describe_object(ns, param)
                collect_anonymous_objects(ns, param, anonymous_objects)
            elif param.get('type') == 'function':
                callback_desc += describe_function(ns, param)
            callback_desc += "</dd></dl>"
            
    if 'returns' in func:
        return_type_desc = describe_type(ns, func['returns'])
        
        callback_desc += '<p>Returns: {}. '.format(return_type_desc)
        if 'description' in func['returns']:
            callback_desc += ' {}'.format(func['returns']['description'])
        callback_desc += '</p>'
        
    print >>out, '<dd>{}</dd>'.format(callback_desc)
        
    if len(extra_params):
        for param in extra_params:
            if param.get('optional', False):
                print >>out, '<dt><code>{}</code>{{{{optional_inline}}}}</dt>'.format(param['name'])
            else:
                print >>out, '<dt><code>{}</code></dt>'.format(param['name'])

            desc = '{}. '.format(describe_type(ns, param))
            desc += param.get('description', '')

            if param.get('type') == 'object':
                desc += describe_object(ns, param)
                collect_anonymous_objects(ns, param, anonymous_objects)

            elif param.get('type') == 'function':
                desc += describe_function(ns, param)
            if desc:
                print >>out, '<dd>{}</dd>'.format(desc)

    print >>out, '</dl>'

    print >>out, '<h3>removeListener(callback)</h3>'
    print >>out, '<p>Stops this listener receiving notifications for this event.</p>'
    print >>out, '<h4>Parameters</h4>'
    print >>out, '<dl>'
    print >>out, '<dt><code>callback</code></dt>'
    print >>out, '<dd><code>Function</code>. The listener to remove.</dd>'
    print >>out, '</dl>'
    
    print >>out, '<h3>hasListener(callback)</h3>'
    print >>out, '<p>Find out whether the given callback is registered as a listener to this event.</p>'
    print >>out, '<h4>Parameters</h4>'
    print >>out, '<dl>'
    print >>out, '<dt><code>callback</code></dt>'
    print >>out, '<dd><code>Function</code>. The listener to check.</dd>'
    print >>out, '</dl>'
    
    print >>out, '<h4>Return value</h4>'
    print >>out, '<p>Boolean: <code>true</code> if the given listener is registered, <code>false</code> otherwise.'

    describe_anonymous_objects(ns, anonymous_objects, out)

    generate_postamble(ns['namespace'], func['name'], func, 'event-', json_name, out)

    out.close()

# We want to preserve the order from the original JSON file.
def json_hook(pairs):
    return collections.OrderedDict(pairs)

def generate(name):
    in_path = os.path.join(in_dir, name + '.json')

    text = open(in_path).read()
    
    # convert inline references from $(ref:<name>) to {{WebExtAPIRef(name)}}
    def convert_reference(match):
        link_text = match.group(1)
        components = link_text.split('.')
        if len(components) > 2:
            link_target = components[0] + "." + components[1]
            remainder = components[2:]
            return "{{{{WebExtAPIRef('{}', '{}', '{}')}}}}".format(link_target, link_target, remainder)
        return "{{{{WebExtAPIRef('{}')}}}}".format(link_text)

    text = re.sub(r'\$\(ref:([^)]*)\)', convert_reference, text)

    # convert inline references from $(topic:<name>) to {{wetopic(name)}}
    def convert_topic(match):
        topic = match.group(2)
        return topic

    text = re.sub(r'<a href=\'\$\(topic:(.*?)\)\'>(.*?)</a>', convert_topic, text)

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
        print >>out, '{'
        print >>out, '"title": "{}",'.format(title)
        print >>out, '"show_toc": 0,'
        print >>out, get_api_tags(out, title)
        print >>out, "}"

        print >>out, '{{AddonSidebar}}'
        print >>out, '<p>{}</p>'.format(ns.get('description', ns['namespace']))

        if 'types' in ns:
            print >>out, '<h2 id="Types">Types</h2>'
            print >>out, '<dl>'
            for t in ns.get('types', []):
                print >>out, '<dt>{{{{WebExtAPIRef("{}.{}")}}}}</dt>'.format(title, t['id'])
                if 'description' in t:
                    print >>out, '<dd>{}</dd>'.format(t['description'])
            print >>out, '</dl>'

        if 'properties' in ns:
            print >>out, '<h2 id="Properties">Properties</h2>'
            print >>out, '<dl>'
            for prop in ns.get('properties', []):
                print >>out, '<dt>{{{{WebExtAPIRef("{}.{}")}}}}</dt>'.format(title, prop)
                if 'description' in ns['properties'][prop]:
                    print >>out, '<dd>{}</dd>'.format(ns['properties'][prop]['description'])
            print >>out, '</dl>'

        if 'functions' in ns:
            print >>out, '<h2 id="Functions">Functions</h2>'
            print >>out, '<dl>'
            for func in ns.get('functions', []):
                args = ', '.join([ p['name'] for p in func['parameters'] ])
                print >>out, '<dt>{{{{WebExtAPIRef("{}.{}()")}}}}</dt>'.format(title, func['name'])
                if 'description' in func:
                    print >>out, '<dd>{}</dd>'.format(func['description'])
            print >>out, '</dl>'

        if 'events' in ns:
            print >>out, '<h2 id="Events">Events</h2>'
            print >>out, '<dl>'
            for func in ns.get('events', []):
                args = ', '.join([ p['name'] for p in func.get('parameters', []) ])
                print >>out, '<dt>{{{{WebExtAPIRef("{}.{}")}}}}</dt>'.format(title, func['name'])
                if 'description' in func:
                    print >>out, '<dd>{}</dd>'.format(func['description'])
            print >>out, '</dl>'

        ff_support = "CompatGeckoDesktop('45.0')"
        print >>out, COMPAT_TABLE%(ff_support)
        print >>out, '{{WebExtChromeCompat}}'
        print >>out, '{{WebExtExamples}}'

        generate_acknowledgement(out, name, ns['namespace'])

        out.close()

for name in sys.argv[3:]:
    generate(name)
