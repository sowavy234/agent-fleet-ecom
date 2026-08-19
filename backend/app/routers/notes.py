from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..utils import user_store
from .auth import get_current_user
from pathlib import Path
import json, os
from .. import notifications

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
NOTES_FILE = DATA_DIR / 'notes.json'
NOTIFICATIONS_FILE = DATA_DIR / 'notifications.json'


def _load_notes():
    if not NOTES_FILE.exists():
        return []
    try:
        return json.loads(NOTES_FILE.read_text())
    except Exception:
        return []


def _save_notes(notes):
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


def _append_notification(n):
    existing = []
    if NOTIFICATIONS_FILE.exists():
        try:
            existing = json.loads(NOTIFICATIONS_FILE.read_text())
        except Exception:
            existing = []
    existing.append(n)
    NOTIFICATIONS_FILE.write_text(json.dumps(existing, indent=2))


class NoteCreate(BaseModel):
    to_email: str
    subject: str
    body: str


@router.post('/create')
async def create_note(note: NoteCreate, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    # store note and create a notification entry (email sending may be attempted)
    users = user_store.list_users()
    if note.to_email not in users:
        raise HTTPException(status_code=404, detail='Recipient not found')
    notes = _load_notes()
    entry = {
        'from': user.get('email'),
        'to': note.to_email,
        'subject': note.subject,
        'body': note.body,
    }
    notes.append(entry)
    _save_notes(notes)
    # append notification entry
    notif = {'to': note.to_email, 'subject': note.subject, 'body': note.body}
    _append_notification({'type': 'email', 'payload': notif})

    # attempt to send email in background if SMTP configured
    def _send():
        try:
            notifications.send_email(notif['to'], notif['subject'], notif['body'])
        except Exception:
            pass

    background_tasks.add_task(_send)
    return {'status': 'created'}


@router.get('/list')
async def list_notes(user=Depends(get_current_user)):
    notes = _load_notes()
    # return only notes relevant to this user
    email = user.get('email')
    filtered = [n for n in notes if n.get('to')==email or n.get('from')==email]
    return {'notes': filtered}
