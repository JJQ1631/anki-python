import os
import json
import requests
import pandas as pd

# AnkiConnect API URL
ANKI_CONNECT_URL = "http://localhost:8765"
# 设置Anki媒体库路径
media_folder = "C:\\Users\\17486\\AppData\\Roaming\\Anki2\\账户1\\collection.media"


def invoke(action, params=None):
    return requests.post(ANKI_CONNECT_URL, json.dumps({
        "action": action,
        "params": params,
        "version": 6
    })).json()


def get_all_notes(deck_name):
    response = invoke("findNotes", {
        "query": f"deck:{deck_name}"
    })
    if response.get("error") is not None:
        raise Exception(response["error"])
    return response["result"]


def get_note_info(note_ids):
    response = invoke("notesInfo", {
        "notes": note_ids
    })
    if response.get("error") is not None:
        raise Exception(response["error"])
    return response["result"]


def get_audio_files(media_folder):
    return {f for f in os.listdir(media_folder) if f.endswith('.mp3')}


def check_missing_audio_files(media_folder, deck_name):
    missing_audio_notes = []
    audio_files = get_audio_files(media_folder)
    note_ids = get_all_notes(deck_name)
    notes_info = get_note_info(note_ids)

    for note in notes_info:
        fields = note['fields']
        if "Text" in fields:
            text = fields["Text"]["value"].strip()
            audio_filename = f"{text}.mp3"
            if audio_filename not in audio_files:
                missing_audio_notes.append({
                    "note_id": note["noteId"],
                    "text": text,
                    "audio_filename": audio_filename
                })
    return missing_audio_notes


def export_to_excel(missing_audio_notes, output_file):
    df = pd.DataFrame(missing_audio_notes)
    df.to_excel(output_file, index=False)


if __name__ == "__main__":
    deck_name = "Saladict"  # 请根据需要调整牌组名称
    output_file = "missing_audio_notes.xlsx"
    missing_audio_notes = check_missing_audio_files(media_folder, deck_name)
    export_to_excel(missing_audio_notes, output_file)
    print(f"检查完成，缺少音频文件对应卡片的信息已保存在: {output_file}")
