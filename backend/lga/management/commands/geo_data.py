"""Shared geography loader for the e-Leseni backend.

Reads region → district (council/LGA) → ward data from the
`tanzaniageodata` npm package (GeoJSON files), so backend and frontend
share one source of truth instead of a hardcoded Python list.
"""
import json
import os
from functools import lru_cache

_CANDIDATE_PATHS = [
    # From backend/ up to the monorepo frontend workspace that has the package.
    os.path.join('..', 'frontend', 'node_modules', 'tanzaniageodata', 'Countries', 'Tanzania'),
    os.path.join('frontend', 'node_modules', 'tanzaniageodata', 'Countries', 'Tanzania'),
    os.path.join('..', 'frontend', 'leseni', 'node_modules', 'tanzaniageodata', 'Countries', 'Tanzania'),
    # npm flat installs sometimes hoist to the repo root.
    os.path.join('..', 'node_modules', 'tanzaniageodata', 'Countries', 'Tanzania'),
    os.path.join('node_modules', 'tanzaniageodata', 'Countries', 'Tanzania'),
]


def _data_dir():
    for candidate in _CANDIDATE_PATHS:
        if os.path.isfile(os.path.join(candidate, 'Regions.json')):
            return candidate
    raise FileNotFoundError(
        'tanzaniageodata package not found. Run `npm i tanzaniageodata` in frontend/ first. '
        f'Searched: {_CANDIDATE_PATHS}'
    )


def _load(filename):
    with open(os.path.join(_data_dir(), filename), encoding='utf-8') as fh:
        return json.load(fh)['features']


@lru_cache(maxsize=1)
def region_district_wards():
    """Return a dict: region -> {district_full_name: [ward, ...]}.

    Region names are normalized (\"Dar es Salaam Region\" -> \"Dar es Salaam\") and
    Mjini Magharibi is unified with Unguja Mjini Magharibi so districts from
    both spellings land under one region.
    """
    region_map = {}

    for feature in _load('Regions.json'):
        name = feature['properties'].get('region', '')
        if not name:
            continue
        normalized = name.replace(' Region', '')
        key = 'Unguja Mjini Magharibi' if normalized == 'Mjini Magharibi' else normalized
        region_map.setdefault(key, {})

    for feature in _load('Districts.json'):
        region = feature['properties'].get('region', '').replace(' Region', '')
        district = feature['properties'].get('District', '')
        if not region or not district:
            continue
        key = 'Unguja Mjini Magharibi' if region == 'Mjini Magharibi' else region
        region_map.setdefault(key, {}).setdefault(district, [])

    for feature in _load('Wards.json'):
        district = feature['properties'].get('District', '')
        ward = feature['properties'].get('Ward', '')
        if not district or not ward:
            continue
        for districts in region_map.values():
            if district in districts and ward not in districts[district]:
                districts[district].append(ward)

    return region_map


@lru_cache(maxsize=1)
def region_lga_wards():
    """Return region -> {short_lga_name: [ward, ...]} (suffixes stripped)."""
    result = {}
    for region, districts in region_district_wards().items():
        result[region] = {}
        for full_name, wards in districts.items():
            short = short_lga_name(full_name)
            entry = result[region].setdefault(short, [])
            entry.extend(w for w in wards if w not in entry)
        # Rename regions that use the Zanzibar spelling in our previous seed.
    # Unguja Mjini Magharibi keeps the same name our LGA codes were built on.
    result['Zanzibar - Mjini Magharibi'] = result.pop('Unguja Mjini Magharibi')
    result['Zanzibar - Unguja North'] = result.pop('Unguja Kaskazini')
    result['Zanzibar - Unguja Central/South'] = result.pop('Unguja Kusini')
    result['Zanzibar - Pemba North'] = result.pop('Pemba Kaskazini') if 'Pemba Kaskazini' in result else {}
    result['Zanzibar - Pemba South'] = result.pop('Pemba Kusini')
    return result


def short_lga_name(full_name):
    """Strip 'Municipal'/'District'/'City' suffixes: 'Ilala Municipal' -> 'Ilala'."""
    for suffix in (
        ' Municipal Council',
        ' District Council',
        ' Town Council',
        ' Municipal',
        ' District',
        ' City',
        ' Council',
    ):
        if full_name.endswith(suffix):
            return full_name[: -len(suffix)]
    return full_name
