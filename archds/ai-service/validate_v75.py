from app.digital_twin import scenario_catalog, simulate
from app.devops_lab import generate_delivery
from app.report import pdf_response

req={'project_name':'Validation','description':'secure scalable real-time platform','functional_requirements':['Users register and receive notifications'],'non_functional_requirements':['high availability','low latency','security'],'constraints':['global access'],'technology_preferences':[],'expected_users':100000,'budget':'High'}
c={'candidate_id':'validation','name':'Hybrid','pattern_key':'hybrid','description':'','components':['API Gateway','Identity & Access','Notifications','PostgreSQL'],'scores':{'weighted_total':88,'scalability':90,'performance':86,'reliability':88,'availability':92},'graph':{'nodes':[{'id':'n1','label':'API Gateway','layer':'edge'}]},'requirement_mappings':{'R1':['Notifications']}}
sc=scenario_catalog(req,c)
assert len(sc)==12
assert simulate(req,c,'traffic_surge',0.5)['metrics']['architecture_score'] != simulate(req,c,'traffic_surge',2.0)['metrics']['architecture_score']
d=generate_delivery(req,c); assert d['validation']['passed']
p=pdf_response({'project_name':'Validation','recommendation':c,'candidates':[c],'requirement_profile':req,'research_metrics':{'confidence':90,'requirement_coverage':100,'final_score':88,'pareto_frontier_size':1}})
assert p.body.startswith(b'%PDF')
print('ARCHDS V7.5 validation: PASS')
