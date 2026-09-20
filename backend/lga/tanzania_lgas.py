"""Tanzania administrative divisions: 31 regions with their LGAs.

Sources: PMO-RALG listings (councils per region, post-2012 reorganization).
District councils, municipal councils, township authorities and city
councils are all represented as LGAs, matching how e-Leseni issues
licences at council level.
"""

# Ordered mapping of region -> list of LGA names.
TANZANIA_LGAS: dict[str, list[str]] = {
    'Arusha': [
        'Arusha City', 'Arusha District', 'Karatu', 'Longido', 'Meru', 'Monduli', 'Ngorongoro',
    ],
    'Dar es Salaam': [
        'Ilala', 'Kinondoni', 'Temeke', 'Ubungo', 'Kigamboni',
    ],
    'Dodoma': [
        'Dodoma City', 'Bahi', 'Chamwino', 'Chemba', 'Kondoa', 'Kongwa', 'Mpwapwa',
    ],
    'Geita': [
        'Geita Town', 'Bukombe', 'Chato', 'Mbogwe', 'Nyang\'hwale',
    ],
    'Iringa': [
        'Iringa Municipal', 'Iringa District', 'Kilolo', 'Mafinga', 'Mufindi',
    ],
    'Kagera': [
        'Bukoba Municipal', 'Bukoba District', 'Biharamulo', 'Chato', 'Karagwe',
        'Kyerwa', 'Missenyi', 'Muleba', 'Muleba South', 'Ngara',
    ],
    'Katavi': [
        'Mpanda Municipal', 'Mlele', 'Nsimbo',
    ],
    'Kigoma': [
        'Kigoma Municipal', 'Buhigwe', 'Kakonko', 'Kasulu', 'Kibondo', 'Uvinza',
    ],
    'Kilimanjaro': [
        'Moshi Municipal', 'Moshi District', 'Hai', 'Mwanga', 'Rombo', 'Same', 'Siha',
    ],
    'Lindi': [
        'Lindi Municipal', 'Kilwa', 'Liwale', 'Nachingwea', 'Ruangwa',
    ],
    'Manyara': [
        'Babati Town', 'Babati District', 'Hanang', 'Kiteto', 'Mbulu', 'Simanjiro',
    ],
    'Mara': [
        'Musoma Municipal', 'Musoma District', 'Bunda', 'Butiama', 'Musoma Rural',
        'Nyamagana', 'Rorya', 'Serengeti', 'Tarime',
    ],
    'Mbeya': [
        'Mbeya City', 'Mbeya District', 'Busokelo', 'Chunya', 'Kyela', 'Mbarali',
        'Mbeya Rural', 'Rungwe',
    ],
    'Morogoro': [
        'Morogoro Municipal', 'Morogoro District', 'Gairo', 'Ifakara', 'Kilosa',
        'Malinyi', 'Morogoro Rural', 'Mvomero', 'Ulanga',
    ],
    'Mtwara': [
        'Mtwara Municipal', 'Mtwara District', 'Masasi', 'Masasi Town', 'Nanyumbu', 'Tandahimba',
    ],
    'Mwanza': [
        'Nyamagana', 'Ilemela', 'Buchosa', 'Kwimba', 'Magu', 'Misungwi', 'Sengerema', 'Ukerewe',
    ],
    'Njombe': [
        'Njombe Town', 'Njombe District', 'Ludewa', 'Makambako', 'Makete', 'Wanging\'ombe',
    ],
    'Pwani': [
        'Kibaha Town', 'Bagamoyo', 'Berega', 'Chalinze', 'Kisarawe', 'Mafia', 'Mkuranga', 'Rufiji',
    ],
    'Rukwa': [
        'Sumbawanga Municipal', 'Kalambo', 'Nkasi',
    ],
    'Ruvuma': [
        'Mbinga', 'Mbinga Town', 'Madaba', 'Namtumbo', 'Nyasa', 'Songea City', 'Tunduru',
    ],
    'Shinyanga': [
        'Shinyanga Municipal', 'Kahama Town', 'Kishapu', 'Msalala', 'Ushetu',
    ],
    'Simiyu': [
        'Bariadi', 'Busega', 'Itilima', 'Maswa', 'Meatu',
    ],
    'Singida': [
        'Singida Municipal', 'Iramba', 'Ikungi', 'Manyoni', 'Mkalama',
    ],
    'Songwe': [
        'Vwawa', 'Ileje', 'Mbozi', 'Momba', 'Songwe',
    ],
    'Tabora': [
        'Tabora Municipal', 'Igunga', 'Kaliua', 'Nzega', 'Sikonge', 'Tabora District', 'Urambo', 'Uyui',
    ],
    'Tanga': [
        'Tanga City', 'Handeni', 'Handeni Town', 'Kilindi', 'Korogwe', 'Korogwe Town',
        'Lushoto', 'Muheza', 'Mkinga', 'Pangani',
    ],
    'Zanzibar - Mjini Magharibi': [
        'Mjini', 'Magharibi A', 'Magharibi B',
    ],
    'Zanzibar - Unguja North': [
        'Kaskazini A', 'Kaskazini B',
    ],
    'Zanzibar - Unguja Central/South': [
        'Kati', 'Kusini',
    ],
    'Zanzibar - Pemba North': [
        'Micheweni', 'Wete',
    ],
    'Zanzibar - Pemba South': [
        'Chake Chake', 'Mkoani',
    ],
}

# Region codes used to build unique LGA codes: IL -> Dar es Salaam etc.
REGION_CODES = {
    'Arusha': 'AR', 'Dar es Salaam': 'DS', 'Dodoma': 'DO', 'Geita': 'GE',
    'Iringa': 'IR', 'Kagera': 'KA', 'Katavi': 'KT', 'Kigoma': 'KG',
    'Kilimanjaro': 'KI', 'Lindi': 'LN', 'Manyara': 'MY', 'Mara': 'MR',
    'Mbeya': 'MB', 'Morogoro': 'MO', 'Mtwara': 'MT', 'Mwanza': 'MW',
    'Njombe': 'NJ', 'Pwani': 'PW', 'Rukwa': 'RK', 'Ruvuma': 'RV',
    'Shinyanga': 'SH', 'Simiyu': 'SI', 'Singida': 'SG', 'Songwe': 'SO',
    'Tabora': 'TB', 'Tanga': 'TA',
    'Zanzibar - Mjini Magharibi': 'ZM', 'Zanzibar - Unguja North': 'ZN',
    'Zanzibar - Unguja Central/South': 'ZC', 'Zanzibar - Pemba North': 'ZP',
    'Zanzibar - Pemba South': 'ZS',
}


def lga_code(region: str, name: str) -> str:
    """Deterministic unique code for an LGA, e.g. DS-ILALA, MO-MOSHI-MUNICIPAL."""
    region_code = REGION_CODES.get(region, region[:2].upper())
    slug = (
        name.upper()
        .replace("'", '')
        .replace('/', ' ')
        .replace('-', ' ')
        .replace('(', '')
        .replace(')', '')
        .replace('.', '')
        .replace(',', '')
    )
    slug = '_'.join(slug.split())[:20]
    return f'{region_code}-{slug}'
