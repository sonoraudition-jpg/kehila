"""Convertit un export Overpass (JSON) en data.json compact pour Kehila.
Usage : python3 build_data.py export_overpass.json
"""
import json, re, sys

HABAD = re.compile(r'chabad|habad|lubavitch|loubavitch|חב"ד|חבד', re.I)
KOSHER = re.compile(r'kosher|cacher|casher|kasher', re.I)


def classify(t):
    kosher = t.get('diet:kosher') in ('yes', 'only') or KOSHER.search(t.get('cuisine', ''))
    if t.get('amenity') in ('mikveh', 'mikvah', 'mikve') or t.get('building') == 'mikveh':
        return 'mik'
    if t.get('amenity') == 'place_of_worship' and t.get('religion') == 'jewish':
        s = ' '.join(t.get(k, '') for k in ('denomination', 'name', 'operator'))
        return 'habad' if HABAD.search(s) else 'syn'
    if t.get('religion') == 'jewish' and HABAD.search(t.get('name', '')):
        return 'habad'
    if t.get('amenity') in ('school', 'kindergarten', 'college') and t.get('religion') == 'jewish':
        return 'school'
    if kosher and t.get('amenity') in ('restaurant', 'fast_food', 'cafe', 'ice_cream', 'bar'):
        return 'resto'
    if kosher and (t.get('shop') or t.get('craft')):
        return 'shop'
    return None


DEFAULT = {'syn': 'Synagogue', 'habad': 'Beth Habad', 'mik': 'Mikvé'}
rows = []
for e in json.load(open(sys.argv[1]))['elements']:
    t = e.get('tags', {})
    cat = classify(t)
    lat = e.get('lat', e.get('center', {}).get('lat'))
    lon = e.get('lon', e.get('center', {}).get('lon'))
    if not cat or lat is None:
        continue
    street = ' '.join(x for x in (t.get('addr:housenumber'), t.get('addr:street')) if x)
    addr = ', '.join(x for x in (street, t.get('addr:city')) if x)
    rows.append([
        cat, round(lat, 6), round(lon, 6),
        t.get('name') or t.get('name:fr') or t.get('name:he') or DEFAULT.get(cat, 'Lieu sans nom'),
        addr or None, t.get('phone') or t.get('contact:phone'),
        t.get('website') or t.get('contact:website'), t.get('opening_hours'), t.get('denomination'),
        t.get('kosher:certification') or t.get('diet:kosher:certification') or t.get('kashrut'),
        f"{e['type']}/{e['id']}",
    ])
json.dump(rows, open('data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print(len(rows), Counter(r[0] for r in rows))
