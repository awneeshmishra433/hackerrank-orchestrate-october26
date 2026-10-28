import re

class IntentClassifier:
    """
    Classifies whether request_text represents an authorized deletion request
    or a non-deletion request (access, correction, export, opt-out) which is NOT_APPLICABLE.
    """
    
    NON_DELETION_PATTERNS = [
        r'\bleave the account active\b',
        r'\bnot asking for deletion\b',
        r'\bkeep the account as it is\b',
        r'\bdo not close the account\b',
        r'\bwithout removing any of my records\b',
        r'\bmarketing lists only\b',
        r'\bthis is an information request\b',
        r'\bleave my profile and purchase history in place\b',
        r'\bi want to continue using the service\b',
        r"\bplease don't delete or change anything\b",
        r'\bstop the promotional emails\b',
        r'\bdownload my account information\b',
        r'\bportable format\b',
        r'\bresetting the login\b',
        r'\bmisspelled.*correct it\b',
        r'\bcopy of last year.*invoices\b',
        r'\bchange the email address used for this account\b',
        r'\bcopy of the information held on my account\b'
    ]

    DELETION_KEYWORDS = [
        'delet',      # matches delete, deleting, deleted, deletion
        'eras',       # matches erase, erasing, erased, erasure
        'close', 'closed', 'closing',
        'remov',      # matches remove, removing, removed
        'suppress', 'supprimer', 'suppression',
        'exclusão', 'excluir',
        'eliminación', 'eliminar',
        'gone',
        '削除',  # Japanese
        '삭제'   # Korean
    ]

    @classmethod
    def is_deletion_authorized(cls, request_text: str) -> bool:
        if not request_text:
            return False

        lower_text = request_text.lower()

        # Check for explicit non-deletion patterns first
        for pat in cls.NON_DELETION_PATTERNS:
            if re.search(pat, lower_text):
                return False

        # Must have at least one deletion keyword/stem
        for kw in cls.DELETION_KEYWORDS:
            if kw in lower_text:
                return True

        return False

