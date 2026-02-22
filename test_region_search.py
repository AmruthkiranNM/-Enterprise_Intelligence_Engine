from company_discovery.search import search_companies

tests = ['Bangalore', 'Mumbai', 'Pune', 'Hyderabad', 'Delhi', 'London']
for region in tests:
    results = search_companies(region)
    print(f'\n=== {region} ({len(results)} companies) ===')
    for c in results[:4]:
        name = c.get('name', '?')
        ind  = c.get('industry', '?')
        site = c.get('website', '?')
        print(f'  - {name:<30s} [{ind}]  {site}')
