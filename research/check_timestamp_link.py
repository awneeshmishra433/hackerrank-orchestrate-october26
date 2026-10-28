import csv

samples_req = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

for cid in sorted(samples_req.keys(), key=lambda x: int(x.split('_')[1])):
    req = samples_req[cid]
    rep_at = req['reported_at']
    req_at = req['requested_at']
    
    # Check activities with event_time == rep_at or close
    exact_rep = [a for a in activities if a['event_time'] == rep_at]
    exact_req = [a for a in activities if a['event_time'] == req_at]
    
    print(f"{cid}: rep_at={rep_at} -> matching acts: {[a['resource_id'] + ' (' + a['event_type'] + ')' for a in exact_rep]}")
