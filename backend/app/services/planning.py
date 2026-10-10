"""Enumerate feasible packages and stress-test ranking against forecast/response assumptions."""
import hashlib
import json
import numpy as np
from app.config import ROOT
from app.services.spatial import distance_km, CONFIG

CATALOG=json.loads((ROOT/'config/interventions.json').read_text())
CATEGORIES=('traffic','industry','dust')


def violations(actions,budget,unavailable,cost_multiplier):
    reasons=[]
    cost=sum(a['cost']*cost_multiplier for a in actions)
    if cost>budget:
        reasons.append(f'Cost ₹{cost:,.0f} exceeds budget ₹{budget:,.0f}')
    for category,limit in CATALOG['limits'].items():
        count=sum(a['category']==category for a in actions)
        if count>limit:
            reasons.append(f'{category}: {count} actions exceeds operational limit {limit}')
    for action in actions:
        if action['id'] in unavailable:
            reasons.append(f"{action['name']} is unavailable")
    return reasons


def optimize(cells,budget=300000,unavailable=(),cost_multiplier=1.,response_multiplier=1.,target_percent=12.,seed=731):
    if not cells:
        raise ValueError('A pollution grid is required')
    actions=CATALOG['actions']
    population=np.array([c['population'] for c in cells],float)
    before=np.array([c['pm25'] for c in cells],float)
    background=np.minimum(before,np.array([c['background'] for c in cells],float))
    shares=np.array([[c['local_weights'][k] for k in CATEGORIES] for c in cells],float)
    spatial_effect=np.zeros((len(actions),len(cells),len(CATEGORIES)))
    for i,a in enumerate(actions):
        kernel=np.array([np.exp(-.5*(distance_km(c['latitude'],c['longitude'],a['latitude'],a['longitude'])/a['radius_km'])**2) for c in cells])
        spatial_effect[i,:,CATEGORIES.index(a['category'])]=kernel*a['cut_percent']/100
    rng=np.random.default_rng(seed)
    scenarios=48
    calibrated=all(c.get('p10') is not None and c.get('p90') is not None for c in cells)
    if calibrated:
        low=np.array([c['p10'] for c in cells]);high=np.array([c['p90'] for c in cells])
        # These are declared stress cases, not a calibrated joint predictive distribution.
        forecast_cases=rng.uniform(low,high,size=(scenarios,len(cells)))
    else:
        forecast_cases=np.tile(before,(scenarios,1))
    response_cases=rng.uniform(.6,1.4,size=(scenarios,len(CATEGORIES)))*response_multiplier
    packages=[]
    caps=np.array([CONFIG['cuts_max'][k]/100 for k in CATEGORIES])
    for mask in range(1<<len(actions)):
        indices=[i for i in range(len(actions)) if mask&(1<<i)]
        chosen=[actions[i] for i in indices]
        if violations(chosen,budget,unavailable,cost_multiplier):
            continue
        cuts=np.minimum(caps,spatial_effect[indices].sum(axis=0)) if indices else np.zeros_like(shares)
        factor=np.minimum(1,np.sum(cuts*shares,axis=1)*CONFIG['pass_through']['central']*response_multiplier)
        reduction=np.maximum(before-background,0)*factor
        uncertain_factor=np.minimum(1,np.sum(cuts[None,:,:]*shares[None,:,:]*response_cases[:,None,:],axis=2)*CONFIG['pass_through']['central'])
        benefit_cases=(np.maximum(forecast_cases-background,0)*uncertain_factor)@population
        packages.append({'id':hashlib.sha256(','.join(a['id'] for a in chosen).encode()).hexdigest()[:12],
                         'actions':chosen,'cost':sum(a['cost']*cost_multiplier for a in chosen),
                         'benefit':float(reduction@population),'worst_case_benefit':float(benefit_cases.min()),
                         'benefit_cases':benefit_cases,'reduction':reduction,
                         'reduction_percent':float(100*(reduction@population)/(before@population)) if before@population else 0})
    packages.sort(key=lambda p:(-p['worst_case_benefit'],p['cost'],p['id']))
    case_winners=np.argmax(np.stack([p['benefit_cases'] for p in packages]),axis=0)
    selected=packages[0]
    def public(p):
        return {k:v for k,v in p.items() if k not in ('benefit_cases','reduction')} | {
            'benefit_low':float(p['benefit_cases'].min()),'benefit_high':float(p['benefit_cases'].max()),
            'affected_areas':[a['name'] for a in p['actions']],
            'budget_remaining':budget-p['cost']}
    after=[{**c,'pm25':float(before[i]-selected['reduction'][i]),'source_type':'modeled'} for i,c in enumerate(cells)]
    perturbed_feasible=[p for p in packages if p['cost']*1.2<=budget]
    cost_choice=perturbed_feasible[0]
    max_reduction=max(p['reduction_percent'] for p in packages)
    rejected=violations(actions,budget,unavailable,cost_multiplier)
    return {'source_type':'modeled','catalog':CATALOG,'budget':budget,'selected':public(selected),
            'alternatives':[public(p) for p in packages[1:4]],'feasible_count':len(packages),
            'rejected_count':(1<<len(actions))-len(packages),
            'rejected_package':{'action_ids':[a['id'] for a in actions],'violations':rejected},
            'cells_before':cells,'cells_after':after,'target_percent':target_percent,
            'target_feasible':max_reduction>=target_percent,'maximum_feasible_reduction_percent':max_reduction,
            'stability':{'same_package_fraction':float(np.mean(case_winners==0)),'stress_cases':scenarios,
                         'forecast_uncertainty_used':calibrated,
                         'status':'stable_under_declared_cases' if calibrated and np.mean(case_winners==0)>=.8 else 'unstable' if calibrated else 'forecast_uncertainty_unavailable'},
            'cost_sensitivity':{'cost_increase_percent':20,'selected_package_id':cost_choice['id'],
                                'changed':cost_choice['id']!=selected['id'],'expenditure':cost_choice['cost']*1.2,
                                'feasible_count':len(perturbed_feasible)},
            'objective':'Maximize the minimum population-weighted modeled 24-hour PM2.5 reduction across declared stress cases.',
            'assumptions':['Intervention costs, source activity and response coefficients are SYNTHETIC assumptions, not measured policy effects.',
                           'Traffic/dust/industry cuts add by category and are capped at the configured limits; regional background cannot be removed.',
                           'Population-weighted benefit has units person·µg/m³ and is not a health outcome.',
                           '48 fixed-seed stress cases vary source response independently by 0.6–1.4; forecast bands are used only when available.',
                           'The stability fraction is the fraction of declared stress cases with the same preferred package, not a causal or probabilistic guarantee.',
                           'Cost sensitivity re-filters the enumerated packages at 20% higher costs; benefits and ranking are unchanged, then the best remaining feasible package is selected.']}
