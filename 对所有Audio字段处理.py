import json
import os
import requests
import pandas as pd
from tqdm import tqdm

# 设置 AnkiConnect 的端口
ANKI_CONNECT_PORT = 8765
MEDIA_FOLDER = r'C:\Users\17486\AppData\Roaming\Anki2\账户1\collection.media'
EXCEL_OUTPUT_PATH = r'C:\Users\17486\Desktop\empty_audio_notes.xlsx'

def invoke(action, params):
    request_json = json.dumps({
        'action': action,
        'version': 6,
        'params': params
    })
    response = requests.post(f'http://localhost:{ANKI_CONNECT_PORT}', data=request_json)
    response_json = json.loads(response.text)
    if len(response_json) != 2:
        raise Exception('响应格式错误')
    if 'error' in response_json:
        if response_json['error'] is not None:
            raise Exception(response_json['error'])
    return response_json['result']

def get_notes(deck_name):
    query = f'deck:{deck_name}'
    note_ids = invoke('findNotes', {'query': query})
    return note_ids

def get_note_fields(note_ids):
    notes = invoke('notesInfo', {'notes': note_ids})
    return notes

def update_audio_field(note_id, value):
    params = {
        'note': {
            'id': note_id,
            'fields': {
                'Audio': value
            }
        }
    }
    invoke('updateNoteFields', params)

def check_and_update_audio(note):
    text = note['fields']['Text']['value']
    note_id = note['noteId']
    audio_filename = f'{text}.mp3'
    audio_path = os.path.join(MEDIA_FOLDER, audio_filename)

    if os.path.isfile(audio_path):
        audio_field_value = f'[sound:{audio_filename}]'
        update_audio_field(note_id, audio_field_value)
        return True
    else:
        update_audio_field(note_id, "")
    return False

def export_to_excel(data, file_path):
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    print(f'导出成功，文件路径：{file_path}')

# 主程序
deck_name = "Saladict"
note_ids = get_notes(deck_name)
notes_info = get_note_fields(note_ids)

empty_audio_notes = []

if notes_info:
    for note in tqdm(notes_info, desc="Checking and updating Audio fields", unit="note"):
        if not check_and_update_audio(note):
            empty_audio_notes.append({
                'Note ID': note['noteId'],
                'Text': note['fields']['Text']['value']
            })

    if empty_audio_notes:
        export_to_excel(empty_audio_notes, EXCEL_OUTPUT_PATH)
    else:
        print("所有卡片的Audio字段已更新。")
else:
    print("没有找到任何笔记。")
