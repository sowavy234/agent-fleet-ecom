from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils import user_store

ADMINS = [
    {"name": "Sean", "email": "sean@example.com", "phone": ""},
    {"name": "Renae", "email": "renae@example.com", "phone": ""},
    {"name": "Andrea", "email": "andrea@example.com", "phone": ""},
]

if __name__ == '__main__':
    created = []
    for a in ADMINS:
        try:
            user_store.create_user(a['name'], a['email'], a.get('phone'))
            created.append(a['email'])
        except ValueError:
            print(f"Skipped existing: {a['email']}")
    print("Seeded:", created)
