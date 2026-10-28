import glob, os
from pypdf import PdfReader

docs = glob.glob('dataset/evidence/documents/*.pdf')
for doc in docs:
    fname = os.path.basename(doc)
    print(f"\n=================== {fname} ===================")
    reader = PdfReader(doc)
    print(f"Num pages: {len(reader.pages)}")
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ({len(text)} chars) ---")
        print(text[:500] if len(text) > 500 else text)

