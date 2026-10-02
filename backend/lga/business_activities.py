"""Council-controlled business activities for Tanzania LGAs.

This is the "kind of business" taxonomy: the activity groups that Tanzanian
local government authorities licence, control and collect levies for under
the Local Government (Business Licensing) and sector by-laws. The list is
seeded into the BusinessActivity table (and remains editable from Django
admin); licence types are tagged with one activity each so the apply wizard
shows the correct licences when an applicant picks a card.

Each entry: (code, name, hint, fee, inspection_required, requirements).
Fee is the default fee in TZS for the per-council licence seeded for the
activity; requirements are (name, kind) pairs using Requirement.Kind values.
"""

from decimal import Decimal

from lga.models import Requirement

# (code, name, description, default_fee, requires_inspection, requirements)
BUSINESS_ACTIVITIES = [
    (
        'FOOD',
        'Food & Beverages',
        'Restaurants, food stalls, butcheries, bakeries, catering and food processing.',
        Decimal('50000'),
        True,
        [
            ('Food Handling Permit', Requirement.Kind.DOCUMENT),
            ('Health Certificate', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'LIQUOR',
        'Liquor, Bars & Nightclubs',
        'Bars, pubs, nightclubs, liquor stores and wholesale liquor dealers.',
        Decimal('150000'),
        True,
        [
            ('Liquor Licence Certificate', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'HOSPITALITY',
        'Hotels & Guest Houses',
        'Hotels, motels, guest houses, lodges and serviced apartments.',
        Decimal('200000'),
        True,
        [
            ('TIN Certificate', Requirement.Kind.DOCUMENT),
            ('Fire & Safety Certificate', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'ENTERTAINMENT',
        'Entertainment & Events',
        'Cinemas, theatres, video shows, public events and amusement centres.',
        Decimal('100000'),
        True,
        [
            ('Event/Entertainment Permit', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'TRANSPORT',
        'Transport & Logistics',
        'Taxis (daladala), buses, trucks, driving schools, garages and freight services.',
        Decimal('100000'),
        False,
        [
            ('Vehicle Registration Copy', Requirement.Kind.DOCUMENT),
            ('Operator Licence', Requirement.Kind.DOCUMENT),
        ],
    ),
    (
        'HEALTH',
        'Health, Pharmacies & Sanitation',
        'Pharmacies, clinics, dispensaries, laboratories, salons, barbers and waste handlers.',
        Decimal('80000'),
        True,
        [
            ('Professional/Operating Licence', Requirement.Kind.DOCUMENT),
            ('Health Certificate', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'LIVESTOCK',
        'Livestock, Fisheries & Agriculture',
        'Slaughterhouses, dairies, butcheries, fish trading, poultry and produce brokers.',
        Decimal('60000'),
        True,
        [
            ('Veterinary/Health Clearance', Requirement.Kind.CLEARANCE),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'NATURAL_RESOURCES',
        'Natural Resources & Mining',
        'Sand mining, gravel, quarrying, timber, charcoal and forest produce trading.',
        Decimal('300000'),
        True,
        [
            ('Environmental Clearance', Requirement.Kind.CLEARANCE),
            ('Land/Plot Agreement', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'INDUSTRY',
        'Small Industries & Workshops',
        'Milling machines, welding, carpentry, garages, mechanics and small-scale manufacturing.',
        Decimal('70000'),
        True,
        [
            ('TIN Certificate', Requirement.Kind.DOCUMENT),
            ('Premises Inspection', Requirement.Kind.INSPECTION),
        ],
    ),
    (
        'MARKETS',
        'Markets & Street Vending',
        'Market stalls, kiosks, hawkers, street vendors and open-air trading.',
        Decimal('20000'),
        False,
        [],
    ),
    (
        'ADVERTISING',
        'Advertisements & Signage',
        'Billboards, posters, signage, radio and street advertising.',
        Decimal('120000'),
        False,
        [
            ('Signage Plan/Sketch', Requirement.Kind.DOCUMENT),
        ],
    ),
    (
        'GENERAL_TRADE',
        'General Trade & Shops',
        'Retail shops, wholesalers, hardware stores, stationary and general merchandise.',
        Decimal('50000'),
        False,
        [
            ('TIN Certificate', Requirement.Kind.DOCUMENT),
            ('Lease Agreement', Requirement.Kind.DOCUMENT),
        ],
    ),
]
