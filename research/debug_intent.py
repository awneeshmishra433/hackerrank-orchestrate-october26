import sys, os
sys.path.insert(0, os.path.abspath('.'))
import re
from code.rule_engine.intent_classifier import IntentClassifier

for cid, text in [
    ('case_04', "I'm deleting my account. You can keep anonymous statistics, but nothing in analytics should still point back to me."),
    ('case_12', "I changed the email on this account before deleting it. Please check that nothing tied to the old address was left behind, even in systems that do not display the email."),
    ('case_26', "I found an old report saying my account still existed. Please check the latest state and confirm that the profile is gone and that remaining records cannot identify me.")
]:
    print(f"\n--- {cid} ---")
    for pat in IntentClassifier.NON_DELETION_PATTERNS:
        if re.search(pat, text.lower()):
            print(f"  Matched non-del pattern: {pat}")
    del_matches = [kw for kw in IntentClassifier.DELETION_KEYWORDS if kw in text.lower()]
    print(f"  Deletion keywords: {del_matches}")
