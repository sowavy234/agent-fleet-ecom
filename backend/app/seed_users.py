from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils import user_store

ADMINS = [
    {"name": "Owner", "email": "owner@example.com", "phone": "+10000000001"},
    {"name": "Admin One", "email": "admin1@example.com", "phone": "+10000000002"},
    {"name": "Admin Two", "email": "admin2@example.com", "phone": "+10000000003"},
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
