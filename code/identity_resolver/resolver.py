from typing import Dict, List, Set, Optional, Any

class IdentityProfile:
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.emails: Set[str] = set()
        self.phones: Set[str] = set()
        self.email_hashes: Set[str] = set()
        self.names: Set[str] = set()
        self.raw_user_record: Optional[Dict[str, Any]] = None

    def match_string(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.strip().lower()
        if self.user_id and self.user_id.lower() == text_lower:
            return True
        if text_lower in self.emails:
            return True
        if text_lower in self.email_hashes:
            return True
        for p in self.phones:
            if p and (p == text.strip() or p.replace(' ', '') == text.replace(' ', '')):
                return True
        for n in self.names:
            if n and n.lower() == text_lower:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'emails': sorted(list(self.emails)),
            'phones': sorted(list(self.phones)),
            'email_hashes': sorted(list(self.email_hashes)),
            'names': sorted(list(self.names))
        }

class IdentityResolver:
    def __init__(self, user_identities: List[Dict[str, Any]], user_audit_logs: List[Dict[str, Any]]):
        self.users_by_email: Dict[str, Dict[str, Any]] = {}
        self.users_by_id: Dict[str, Dict[str, Any]] = {}
        self.user_audit_logs: List[Dict[str, Any]] = user_audit_logs

        for u in user_identities:
            uid = u['user_id']
            email = u['email'].strip().lower() if u.get('email') else ''
            self.users_by_id[uid] = u
            if email:
                self.users_by_email[email] = u

        # Build index from historical email/phone/hash to user_id
        self.historical_email_to_uid: Dict[str, str] = {}
        for a in self.user_audit_logs:
            uid = a['user_id']
            fn = a['field_name']
            if fn == 'email':
                old_val = a.get('old_value', '').strip().lower()
                new_val = a.get('new_value', '').strip().lower()
                if old_val: self.historical_email_to_uid[old_val] = uid
                if new_val: self.historical_email_to_uid[new_val] = uid

    def resolve(self, request_email: str) -> IdentityProfile:
        norm_email = request_email.strip().lower()
        user_record = self.users_by_email.get(norm_email)
        uid = user_record['user_id'] if user_record else None

        if not uid:
            uid = self.historical_email_to_uid.get(norm_email)
            if uid:
                user_record = self.users_by_id.get(uid)

        profile = IdentityProfile(user_id=uid)
        profile.raw_user_record = user_record
        profile.emails.add(norm_email)

        if user_record:
            if user_record.get('email'):
                profile.emails.add(user_record['email'].strip().lower())
            if user_record.get('phone'):
                profile.phones.add(user_record['phone'].strip())
            if user_record.get('email_hash'):
                profile.email_hashes.add(user_record['email_hash'].strip().lower())
            if user_record.get('name'):
                profile.names.add(user_record['name'].strip())

        if uid:
            for a in self.user_audit_logs:
                if a['user_id'] == uid:
                    fn = a['field_name']
                    if fn == 'email':
                        if a.get('old_value'): profile.emails.add(a['old_value'].strip().lower())
                        if a.get('new_value'): profile.emails.add(a['new_value'].strip().lower())
                    elif fn == 'phone':
                        if a.get('old_value'): profile.phones.add(a['old_value'].strip())
                        if a.get('new_value'): profile.phones.add(a['new_value'].strip())
                    elif fn == 'email_hash':
                        if a.get('old_value'): profile.email_hashes.add(a['old_value'].strip().lower())
                        if a.get('new_value'): profile.email_hashes.add(a['new_value'].strip().lower())

        return profile

