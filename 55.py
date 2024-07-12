import requests
from bs4 import BeautifulSoup
import json
import os
import shutil
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from openpyxl import Workbook
from tqdm import tqdm

# 媒体库路径
MEDIA_LIBRARY_PATH = r'path_to_your_media_library'
EXTERNAL_AUDIO_PATH = r'E:\单词语音包'

# AnkiConnect接口
ANKI_CONNECT_URL = 'http://localhost:8765'


def fetch_notes(deck_name):
    payload = {
        'action': 'findNotes',
        'version': 6,
        'params': {
            'query': f'deck:"{deck_name}"'
        }
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()['result']


def fetch_note_fields(note_id):
    payload = {
        'action': 'notesInfo',
        'version': 6,
        'params': {
            'notes': [note_id]
        }
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()['result'][0]


def get_ipa_from_cambridge(word):
    url = f'https://dictionary.cambridge.org/dictionary/english/{word}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    ipa_us = soup.find('span', class_='ipa dipa lpr-2 lpl-1')
    ipa_uk = soup.find('span', class_='ipa dipa lpr-2 lpl-1')

    ipa_us_text = ipa_us.text if ipa_us else None
    ipa_uk_text = ipa_uk.text if ipa_uk else None

    return ipa_us_text, ipa_uk_text


def find_audio_file(word):
    audio_path = None
    for ext in ['.mp3', '.wav']:
        audio_file = os.path.join(MEDIA_LIBRARY_PATH, f'{word}{ext}')
        if os.path.exists(audio_file):
            audio_path = audio_file
            break
        audio_file = os.path.join(EXTERNAL_AUDIO_PATH, f'{word}{ext}')
        if os.path.exists(audio_file):
            audio_path = audio_file
            shutil.copy(audio_file, MEDIA_LIBRARY_PATH)
            break
    return audio_path


def update_note_fields(note_id, updated_fields):
    payload = {
        'action': 'updateNoteFields',
        'version': 6,
        'params': {
            'note': {
                'id': note_id,
                'fields': updated_fields
            }
        }
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()


def process_note(note_id):
    note = fetch_note_fields(note_id)
    fields = note['fields']
    text_field = fields.get('Text', {}).get('value', '').strip()
    context_field = fields.get('Context', {}).get('value', '').strip()

    if not text_field:
        return None, None

    word = text_field.split()[0]
    ipa_us, ipa_uk = get_ipa_from_cambridge(word)
    audio_file = find_audio_file(word)
    audio_field = f'[sound:{os.path.basename(audio_file)}]' if audio_file else ''

    updated_fields = {}
    if not fields.get('American IPA', {}).get('value'):
        updated_fields['American IPA'] = ipa_us
    if not fields.get('British IPA', {}).get('value'):
        updated_fields['British IPA'] = ipa_uk
    if not fields.get('Audio', {}).get('value'):
        updated_fields['Audio'] = audio_field

    if updated_fields:
        update_note_fields(note_id, updated_fields)
        return text_field, updated_fields
    else:
        return text_field, None


def main():
    deck_name = 'Saladict'
    notes = fetch_notes(deck_name)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_note, note_id): note_id for note_id in notes}
        results = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            note_id = futures[future]
            try:
                text_field, updated_fields = future.result()
                if text_field and updated_fields:
                    print(f'Note {note_id}: {text_field} updated to {updated_fields}')
                elif text_field:
                    print(f'Note {note_id}: {text_field} not updated')
                else:
                    print(f'Note {note_id} has empty Text field')
            except Exception as e:
                print(f'Error processing note {note_id}: {e}')


if __name__ == "__main__":
    main()
