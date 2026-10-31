"""Mirror the WoodMart Elementor template library into this repository.

Step 1 (templates): python tools/mirror.py templates
Step 2 (media):     python tools/mirror.py media
Step 3 (index):     python tools/mirror.py index

Templates are saved as templates/<id>.json with every image URL rewritten to {{LIB}}/media/<path>,
so the theme can point them at wherever this repository is served from.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_URL = 'https://woodmart.xtemos.com/wp-admin/admin-ajax.php?action=woodmart_load_templates&builder=elementor'
ITEM_URL = 'https://woodmart.xtemos.com/?woodmart_action=woodmart_get_template&id=%s'
UA = 'FusionX library mirror (one-time copy, throttled)'
MEDIA_RE = re.compile(r'https?:(?:\\?/){2}([a-z0-9.-]*(?:xtemos\.com|b-cdn\.net))((?:\\?/)[^"\'\s)]+?\.(?:jpe?g|png|gif|svg|webp|mp4|webm|json))', re.I)


def get(url, binary=False, tries=4):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            return data if binary else data.decode('utf-8')
        except Exception as e:  # noqa: BLE001
            if n == tries - 1:
                raise
            time.sleep(3 * (n + 1))


def media_path(host, path):
    path = path.replace('\\/', '/')
    return host + urllib.parse.unquote(path)


def templates():
    os.makedirs(os.path.join(ROOT, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'templates'), exist_ok=True)
    lst = json.loads(get(LIST_URL))
    json.dump(lst, open(os.path.join(ROOT, 'raw', 'list.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    done = 0
    for el in lst['elements']:
        out = os.path.join(ROOT, 'templates', '%s.json' % el['id'])
        if os.path.exists(out):
            continue
        d = json.loads(get(ITEM_URL % el['id']))
        cfg = d['element'].get('config_elementor') or ''
        content = json.loads(cfg) if cfg else {'content': []}
        t = json.dumps(content, ensure_ascii=False)
        t = MEDIA_RE.sub(lambda m: '{{LIB}}/media/' + media_path(m.group(1), m.group(2)), t)
        open(out, 'w', encoding='utf-8').write(t)
        done += 1
        print('template', el['id'], el['slug'], flush=True)
        time.sleep(0.8)
    print('templates fetched:', done)


def media():
    urls = set()
    lst = json.load(open(os.path.join(ROOT, 'raw', 'list.json'), encoding='utf-8'))
    for el in lst['elements']:
        m = MEDIA_RE.search(el.get('image', ''))
        if m:
            urls.add(('https://' + m.group(1) + m.group(2).replace('\\/', '/'), media_path(m.group(1), m.group(2))))
    raw_urls = {}
    for f in os.listdir(os.path.join(ROOT, 'templates')):
        t = open(os.path.join(ROOT, 'templates', f), encoding='utf-8').read()
        for p in re.findall(r'\{\{LIB\}\}/media/([^"\']+)', t):
            raw_urls[p] = p
    for p in raw_urls:
        host, _, rest = p.partition('/')
        urls.add(('https://' + host + '/' + rest, p))
    print('media files:', len(urls), flush=True)
    missing = []
    for url, p in sorted(urls):
        out = os.path.join(ROOT, 'media', p)
        if os.path.exists(out):
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        try:
            data = get(urllib.parse.quote(url, safe=':/?=&%'), binary=True)
        except Exception as e:  # noqa: BLE001
            try:
                data = get(urllib.parse.quote(url.replace('https://', 'http://', 1), safe=':/?=&%'), binary=True)
            except Exception as e2:  # noqa: BLE001
                missing.append((url, str(e2)[:80]))
                print('MISSING', url, str(e2)[:80], flush=True)
                continue
        open(out, 'wb').write(data)
        print('media', p, len(data), flush=True)
        time.sleep(0.25)
    json.dump(missing, open(os.path.join(ROOT, 'raw', 'missing-media.json'), 'w'), indent=1)
    print('missing:', len(missing))


def index():
    lst = json.load(open(os.path.join(ROOT, 'raw', 'list.json'), encoding='utf-8'))
    items = []
    for el in lst['elements']:
        tags = [c[4:] for c in el.get('class', '').split() if c.startswith('tag-') and c != 'tag-all']
        m = MEDIA_RE.search(el.get('image', ''))
        items.append({
            'id': str(el['id']), 'title': el['title'], 'slug': el['slug'], 'tags': tags,
            'image': ('{{LIB}}/media/' + media_path(m.group(1), m.group(2))) if m else '',
        })
    tags = [{'slug': t['slug'] if 'slug' in t else t.get('value', ''), 'title': t.get('title', t.get('name', ''))} for t in lst.get('tags', [])]
    json.dump({'version': time.strftime('%Y-%m-%d'), 'tags': tags, 'templates': items},
              open(os.path.join(ROOT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('index:', len(items), 'templates,', len(tags), 'tags')


if __name__ == '__main__':
    {'templates': templates, 'media': media, 'index': index}[sys.argv[1]]()
