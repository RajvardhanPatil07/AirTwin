"""Enumerate feasible packages and stress-test ranking against forecast/response assumptions."""
import hashlib
import json
import numpy as np
from app.config import ROOT
from app.services.spatial import distance_km, CONFIG

CATALOG=json.loads((ROOT/'config/interventions.json').read_text())
EVIDENCE=json.loads((ROOT/'config/interventions-evidence.json').read_text())
CATALOG['evidence_sources']=EVIDENCE['sources']
for action in CATALOG['actions']:
    action.update(EVIDENCE['actions'][action['id']])
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


def optimize(cells,budget=300000,unavailable=(),cost_multiplier=1.,response_multiplier=1.,target_percent=12.,seed=731,preference='robust'):
    if preference not in ('robust','max_benefit','min_cost'):
        raise ValueError('Unknown planning preference')
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
    operational=[]
    caps=np.array([CONFIG['cuts_max'][k]/100 for k in CATEGORIES])
    for mask in range(1<<len(actions)):
        indices=[i for i in range(len(actions)) if mask&(1<<i)]
        chosen=[actions[i] for i in indices]
        if violations(chosen,float('inf'),unavailable,cost_multiplier):
            continue
        cuts=np.minimum(caps,spatial_effect[indices].sum(axis=0)) if indices else np.zeros_like(shares)
        factor=np.minimum(1,np.sum(cuts*shares,axis=1)*CONFIG['pass_through']['central']*response_multiplier)
        reduction=np.maximum(before-background,0)*factor
        envelope=[]
        for edge in ('low','high'):
            envelope_cuts=sum((spatial_effect[i]*actions[i].get('response_range_percent',{}).get(edge,actions[i]['cut_percent'])/actions[i]['cut_percent'] for i in indices),np.zeros_like(shares))
            envelope_factor=np.minimum(1,np.sum(np.minimum(caps,envelope_cuts)*shares,axis=1)*CONFIG['pass_through']['central']*response_multiplier)
            envelope.append(float((np.maximum(before-background,0)*envelope_factor)@population))
        uncertain_factor=np.minimum(1,np.sum(cuts[None,:,:]*shares[None,:,:]*response_cases[:,None,:],axis=2)*CONFIG['pass_through']['central'])
        benefit_cases=(np.maximum(forecast_cases-background,0)*uncertain_factor)@population
        operational.append({'id':hashlib.sha256(','.join(a['id'] for a in chosen).encode()).hexdigest()[:12],
                         'actions':chosen,'cost':sum(a['cost']*cost_multiplier for a in chosen),
                         'benefit':float(reduction@population),'worst_case_benefit':float(benefit_cases.min()),
                         'benefit_cases':benefit_cases,'reduction':reduction,
                         'response_envelope_low_percent':100*envelope[0]/float(before@population) if before@population else 0.,
                         'response_envelope_high_percent':100*envelope[1]/float(before@population) if before@population else 0.,
                         'reduction_percent':float(100*(reduction@population)/(before@population)) if before@population else 0})
    packages=[p for p in operational if p['cost']<=budget]
    packages.sort(key=lambda p:(-p['worst_case_benefit'],-p['benefit'],p['cost'],p['id']))
    max_reduction=max(p['reduction_percent'] for p in packages)
    target_packages=[p for p in packages if p['reduction_percent']>=target_percent]
    candidates=target_packages or packages
    case_winners=np.argmax(np.stack([p['benefit_cases'] for p in candidates]),axis=0)
    robust=candidates[0]
    maximum=max(packages,key=lambda p:(p['benefit'],-p['cost'],p['id']))
    cheapest=min(target_packages,key=lambda p:(p['cost'],-p['worst_case_benefit'],p['id'])) if target_packages else None
    selected={'robust':robust,'max_benefit':maximum,'min_cost':cheapest or robust}[preference]
    selected_index=next((i for i,p in enumerate(candidates) if p['id']==selected['id']),None)
    def public(p):
        return {k:v for k,v in p.items() if k not in ('benefit_cases','reduction')} | {
            'benefit_low':float(p['benefit_cases'].min()),'benefit_high':float(p['benefit_cases'].max()),
            'affected_areas':list(dict.fromkeys(a['name'].split(' ')[0] for a in p['actions'])),
            'budget_remaining':budget-p['cost']}
    after=[{**c,'pm25':float(before[i]-selected['reduction'][i]),'source_type':'modeled'} for i,c in enumerate(cells)]
    perturbed_feasible=[p for p in packages if p['cost']*1.2<=budget]
    perturbed_target=[p for p in perturbed_feasible if p['reduction_percent']>=target_percent]
    cost_choice=(max(perturbed_feasible,key=lambda p:(p['benefit'],-p['cost'],p['id'])) if preference=='max_benefit' else
                 min(perturbed_target,key=lambda p:(p['cost'],-p['worst_case_benefit'],p['id'])) if preference=='min_cost' and perturbed_target else
                 (perturbed_target or perturbed_feasible)[0])
    recommendations=[
        {'kind':'robust','label':'Strongest under stress','package':public(robust),
         'reason':'Largest minimum modeled benefit in conditional operating stress cases, meeting the central target when feasible. Complete implementation failure can still yield zero benefit.'},
        {'kind':'max_benefit','label':'Maximum modeled benefit','package':public(maximum),
         'reason':'Largest central population-weighted reduction within the budget and operational limits.'},
        {'kind':'min_cost','label':'Lowest cost meeting target','package':public(cheapest) if cheapest else None,
         'reason':'Lowest expenditure meeting the central target.' if cheapest else 'No package within this budget meets the central target.'}]
    denominator=float(before@population)
    def percent(benefit):
        return 100*float(benefit)/denominator if denominator else 0.
    operational_target=[p for p in operational if p['reduction_percent']>=target_percent]
    minimum_budget=min((p['cost'] for p in operational_target),default=None)
    selected_cuts=np.zeros_like(shares)
    for a in selected['actions']:
        selected_cuts+=spatial_effect[actions.index(a)]
    selected_cuts=np.minimum(caps,selected_cuts)
    category_factors=selected_cuts*shares*CONFIG['pass_through']['central']*response_multiplier
    category_factors/=np.maximum(1,category_factors.sum(axis=1))[:,None]
    explanation={
        'background_share_percent':percent(background@population),
        'local_excess_share_percent':percent(np.maximum(before-background,0)@population),
        'weighted_baseline_pm25':float(before@population/population.sum()) if population.sum() else 0.,
        'available_actions_maximum_percent':max(p['reduction_percent'] for p in operational),
        'minimum_budget_for_target':minimum_budget,
        'target_gap_percent':max(0,target_percent-max_reduction),
        'unavailable_action_count':len(set(unavailable)),
        'limiting_reason':'target_met' if max_reduction>=target_percent else 'budget' if minimum_budget is not None else 'action_scope_and_background',
        'category_reductions':[{'category':k,'reduction_percent':percent((np.maximum(before-background,0)*category_factors[:,j])@population)} for j,k in enumerate(CATEGORIES)],
        'notes':['Regional background is assumed and cannot be removed by these local actions.',
                 'Influence decays with distance through an assumed Gaussian radius; this is not a measured treatment boundary.',
                 'Source shares, category caps and pass-through limit the response. These are scenario assumptions.',
                 'The available-action ceiling keeps operational limits and unavailable actions but removes the budget limit.']}
    selected_reason=next(r['reason'] for r in recommendations if r['kind']==preference)
    if preference=='min_cost' and cheapest is None:
        selected_reason+=' Showing the strongest package under stress instead.'
    rejected=violations(actions,budget,unavailable,cost_multiplier)
    return {'source_type':'modeled','catalog':CATALOG,'budget':budget,'selected':public(selected),
            'preference':preference,'recommendations':recommendations,'selected_reason':selected_reason,'explanation':explanation,
            'alternatives':[public(p) for p in packages if p['id']!=selected['id']][:3],'feasible_count':len(packages),
            'rejected_count':(1<<len(actions))-len(packages),
            'rejected_package':{'action_ids':[a['id'] for a in actions],'violations':rejected},
            'cells_before':cells,'cells_after':after,'target_percent':target_percent,
            'target_feasible':max_reduction>=target_percent,'maximum_feasible_reduction_percent':max_reduction,
            'stability':{'same_package_fraction':float(np.mean(case_winners==selected_index)) if selected_index is not None else 0.,'stress_cases':scenarios,
                         'forecast_uncertainty_used':calibrated,
                         'status':'stable_under_declared_cases' if calibrated and selected_index is not None and np.mean(case_winners==selected_index)>=.8 else 'unstable' if calibrated else 'forecast_uncertainty_unavailable'},
            'cost_sensitivity':{'cost_increase_percent':20,'selected_package_id':cost_choice['id'],
                                'changed':cost_choice['id']!=selected['id'],'expenditure':cost_choice['cost']*1.2,
                                'feasible_count':len(perturbed_feasible)},
            'objective':'Maximize the minimum population-weighted modeled PM2.5 reduction across declared stress cases among packages meeting the nominal target, when feasible.',
            'assumptions':['Intervention costs, source activity and response coefficients are SYNTHETIC assumptions, not measured policy effects.',
                           'Primary policy sources support action context. Exact comparable local operating quotes are unverified; cost entries remain scenario assumptions.',
                           'Action response envelopes include zero effect. The ranking stress cases condition on operation at 0.6–1.4 of central response; they are not a guarantee against implementation failure.',
                           'The target applies to the central modeled reduction, not every stress case. If infeasible, the package with the largest minimum stress-case benefit is selected.',
                           'Traffic/dust/industry cuts add by category and are capped at the configured limits; regional background cannot be removed.',
                           'Population-weighted benefit has units person·µg/m³ and is not a health outcome.',
                           '48 fixed-seed stress cases vary source response independently by 0.6–1.4; forecast bands are used only when available.',
                           'The stability fraction is the fraction of declared stress cases with the same preferred package, not a causal or probabilistic guarantee.',
                           'Cost sensitivity re-filters the enumerated packages at 20% higher costs; benefits and ranking are unchanged, then the best remaining feasible package is selected.']}
