"""
Transaction tag groups and categorisations.

Transactions are first grouped into income, spending, and transfers. Within
those groups, they are then grouped further (e.g. spend into Lloyds categories).
All groupings are based on tag_auto. 

"""

tag_groups = {
    # tag categorisation into main groups

    'income': [
        'benefits',
        'bond income',
        'bursary',
        'dividend',
        'family benefits',
        'incapacity benefits',
        'interest income',
        'investment income - other',
        'irregular income or gifts',
        'job seekers benefits',
        'loan or credit income',
        'miscellaneous income - other',
        'other benefits',
        'pension - other',
        'pension or investments',
        'pension',
        'rental income (room)',
        'rental income (whole property)',
        'rental income'
        'salary (secondary)',
        'salary or wages (main)',
        'salary or wages (other)',
        'state pension',
        'student loan funds',
        'unsecured loan funds',
        'winnings',
        'work pension',
    ],

    'spend': [
        'accessories',
        'administration - other',
        'alcohol',
        'appearance',
        'appliances or electrical',
        'art supplies',
        'art',
        'bank charges',
        'banking charges',
        'beauty products',
        'beauty treatments',
        'bills',
        'books / magazines / newspapers',
        'breakdown cover',
        'broadband',
        'business expenses',
        'cash',
        'charity - other',
        'child - clothes',
        'child - everyday or childcare',
        'child - toys, clubs or other',
        'childcare fees',
        'children - other',
        'childrens club fees',
        'cinema',
        'clothes - designer or other',
        'clothes - everyday or work',
        'clothes - other',
        'clothes',
        'coal/oil/lpg/other',
        'concert & theatre',
        'contents or other insurance',
        'council tax',
        'course and tuition fees',
        'cycling',
        'dental insurance',
        'dental treatment',
        'designer clothes',
        'device rental',
        'dining and drinking',
        'dining or going out',
        'diy',
        'donation to organisation',
        'driving lessons',
        'dry cleaning and laundry',
        'education - other',
        'electrical equipment',
        'electricity',
        'energy (gas, elec, other)',
        'enjoyment',
        'entertainment, tv, media',
        'expenses',
        'eye care',
        'financial - other',
        'fines',
        'flights',
        'flowers',
        'food, groceries, household',
        'fuel',
        'furniture',
        'furniture, furnishing, gardens',
        'gambling',
        'games and gaming',
        'garden',
        'gas and electricity',
        'gas',
        'gifts - other',
        'gifts or presents',
        'groceries',
        'gym membership',
        'hairdressing',
        'hairdressing, health, other',
        'health insurance',
        'hire purchase',
        'hobbies - other',
        'hobbies or activities',
        'hobby club membership',
        'hobby supplies',
        'holiday',
        'holidays',
        'home and garden - other',
        'home appliance insurance',
        'home diy or repairs',
        'home insurance',
        'home',
        'hotel/b&b',
        'household - other',
        'income insurance',
        'insurance - other',
        'insurance',
        'interest charges',
        'jewellery',
        'legal',
        'life insurance',
        'lifestyle - other',
        'lighting',
        'lunch or snacks',
        'media bundle',
        'medical treatment',
        'medical, dental, eye care',
        'memberships',
        'mobile app',
        'mobile phone insurance',
        'mobile',
        'mortgage or rent',
        'mortgage payment',
        'mortgage release',
        'motorbike insurance',
        'museum/exhibition',
        'music',
        'musical equipment',
        'one-off or other payment',
        'one-off or other',
        'parking or tolls',
        'parking',
        'payday loan funds',
        'payday loan',
        'payment protection insurance',
        'penalty charges',
        'personal care - other',
        'personal electronics',
        'personal loan',
        'pet - everyday or food',
        'pet - toys, training, other',
        'pet insurance',
        'phone (landline)',
        'phone or internet',
        'photography',
        'physiotherapy',
        'postage / shipping',
        'printing',
        'public transport',
        'refunded purchase',
        'rent',
        'repayments',
        'rewards/cashback',
        'road charges',
        'school fees',
        'secured loan repayment',
        'service / parts / repairs',
        'sharedealing account',
        'shoes',
        'social club',
        'software',
        'spa',
        'sports club membership',
        'sports equipment',
        'sports event',
        'stationery & consumables',
        'stationery',
        'store card repayment',
        'student loan repayment',
        'supermarket',
        'take-away',
        'tax payment',
        'taxi',
        'taxis or vehicle hire',
        'toiletries',
        'toys',
        'tradesmen fees',
        'transport',
        'tv / movies package',
        'tv licence',
        'unsecured loan repayment',
        'vehicle hire',
        'vehicle insurance',
        'vehicle running costs',
        'vehicle tax',
        'vehicle',
        'vet',
        'water',
        'web hosting',
        'zoo/theme park'
    ],

    'transfer': [
        'car fund',
        'credit card repayment',
        'credit card',
        'current account',
        'general savings',
        'investment - other',
        'investments or shares',
        'isa',
        'paypal account',
        'saving (general)',
        'savings (general)',
        'savings',
        'transfers',
    ],
}


custom_transfers = {
    'savings': [
        'general savings',
        'investment - other',
        'investments or shares',
        'isa',
        'saving (general)',
        'savings (general)',
        'savings',
    ],

    'transfer': [
        'car fund',
        'credit card repayment',
        'credit card',
        'current account',
        'paypal account',
        'transfers',
    ],
}


lloyds_spend = {
    # spend grouping based on lloyds banking group, from muggleton2021evidence
    # changes: dropped miscellaneous category
    
    'communication': [
        'media bundle',
        'mobile',
        'mobile app',
        'phone (landline)',
        'phone or internet',
        'tv / movies package',
        'tv licence',
    ],
    
    'finance': [
        'bank charges',
        'banking charges',
        'breakdown cover',
        'financial - other',
        'fines',
        'interest charges',
        'payday loan',
        'payday loan funds',
        'mobile phone insurance',
        'home appliance insurance',
        'contents or other insurance',
        'dental insurance',
        'health insurance',
        'home insurance',
        'income insurance',
        'insurance',
        'insurance - other',
        'life insurance',
        'motorbike insurance',
        'payment protection insurance',
        'pet insurance',
        'vehicle insurance',
        'penalty charges',
        'personal loan',
        'repayments',
        'rewards/cashback',
        'secured loan repayment',
        'sharedealing account',
        'student loan repayment',
        'unsecured loan repayment',
        'web hosting',
    ],
    
    'hobbies': [
        'art',
        'art supplies',
        'cycling',
        'gym membership',
        'hobbies - other',
        'hobbies or activities',
        'hobby club membership',
        'hobby supplies',
        'memberships',
        'museum/exhibition',
        'music',
        'musical equipment',
        'photography',
        'spa',
        'sports club membership',
        'sports equipment',
    ],
    
    'household': [
        'alcohol',
        'appliances or electrical',
        'bills',
        'broadband',
        'coal/oil/lpg/other',
        'diy',
        'electricity',
        'energy (gas, elec, other)',
        'flowers',
        'food, groceries, household',
        'furniture',
        'furniture, furnishing, gardens',
        'garden',
        'fuel',
        'gas',
        'gas and electricity',
        'groceries',
        'home',
        'home and garden - other',
        'home diy or repairs',
        'household - other',
        'lighting',
        'mortgage or rent',
        'mortgage payment',
        'mortgage release',
        'rent',
        'supermarket',
        'tax payment',
        'toiletries',
        'water',
    ],
        
    'motor': [
        'driving lessons',
        'parking',
        'parking or tolls',
        'road charges',
        'vehicle',
        'vehicle hire',
        'vehicle running costs',
        'vehicle tax',
    ],
    
    'retail': [
        'accessories',
        'appearance',
        'beauty products',
        'beauty treatments',
        'books / magazines / newspapers',
        'child - clothes',
        'child - everyday or childcare',
        'child - toys, clubs or other',
        'clothes',
        'clothes - designer or other',
        'clothes - everyday or work',
        'clothes - other',
        'designer clothes',
        'hairdressing, health, other',
        'jewellery',
        'lifestyle - other',
        'personal care - other',
        'personal electronics',
        'pet - everyday or food',
        'pet - toys, training, other',
        'refunded purchase',
        'shoes',
        'software',
        'stationery',
        'stationery & consumables',
        'store card repayment',
        'toys',
        'vet',
    ],
    
    'services': [
        'childcare fees',
        'childrens club fees',
        'cinema',
        'concert & theatre',
        'council tax',
        'course and tuition fees',
        'dental treatment',
        'dining and drinking',
        'dining or going out',
        'dry cleaning and laundry',
        'education - other',
        'enjoyment',
        'entertainment, tv, media',
        'eye care',
        'gambling',
        'games and gaming',
        'hairdressing',
        'hire purchase',
        'hotel/b&b',
        'legal',
        'lunch or snacks',
        'medical treatment',
        'medical, dental, eye care',
        'physiotherapy',
        'postage / shipping',
        'printing',
        'school fees',
        'service / parts / repairs',
        'sports event',
        'take-away',
        'tradesmen fees',
        'zoo/theme park'
    ],
    
    'travel': [
        'flights',
        'holiday',
        'holidays',
        'public transport',
        'taxi',
        'taxis or vehicle hire',
        'transport',
    ],
    
    'other_spend': [
        'administration - other',
        'business expenses',
        'cash',
        'charity - other',
        'children - other',
        'device rental',
        'donation to organisation',
        'electrical equipment',
        'expenses',
        'gifts - other',
        'gifts or presents',
        'one-off or other',
        'one-off or other payment',
        'social club',
    ],
}


hacioglu_income = {
    # income categorisation following haciouglu2020evidence
    # added unsecured load funds, winnings, and bursary to
    # other income.

    'earnings': [
        'salary or wages (main)',
        'salary or wages (other)',
        'salary (secondary)',
    ],

    'pensions': [
        'pension - other',
        'pension',
        'work pension',
        'state pension',
        'pension or investments',
    ],

    'benefits': [
        'benefits',
        'family benefits',
        'job seekers benefits',
        'other benefits',
        'incapacity benefits'
    ],

    'other_income': [
        'rental income (whole property)',
        'rental income (room)',
        'rental income',
        'irregular income or gifts',
        'miscellaneous income - other',
        'investment income - other',
        'loan or credit income',
        'bond income',
        'interest income',
        'dividend',
        'student loan funds',
        'unsecured loan funds',
        'winnings',
        'bursary',
    ],
}

