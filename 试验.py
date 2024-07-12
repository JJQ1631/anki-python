import requests
import json
import concurrent.futures
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
import re
import pandas as pd
import nltk
from tqdm import tqdm

# Ensure NLTK data packages are downloaded
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Define AnkiConnect endpoint
ANKI_CONNECT_URL = 'http://localhost:8765'

# Function to fetch notes from AnkiConnect
def fetch_notes():
    payload = json.dumps({
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": "deck:Saladict"
        }
    })
    response = requests.post(ANKI_CONNECT_URL, data=payload)
    return json.loads(response.text)['result']

# Function to fetch note fields from AnkiConnect
def fetch_note_fields(note_ids):
    payload = json.dumps({
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    })
    response = requests.post(ANKI_CONNECT_URL, data=payload)
    return json.loads(response.text)['result']

# Function to update a note field in AnkiConnect
def update_note_field(note_id, field, value):
    payload = json.dumps({
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    field: value
                }
            }
        }
    })
    response = requests.post(ANKI_CONNECT_URL, data=payload)
    return response.json()

# Function to convert POS tags to WordNet format
def get_wordnet_pos(pos_tag):
    if pos_tag.startswith('J'):
        return wordnet.ADJ
    elif pos_tag.startswith('V'):
        return wordnet.VERB
    elif pos_tag.startswith('N'):
        return wordnet.NOUN
    elif pos_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

# Function to clean and lemmatize text
def clean_and_lemmatize(text, context):
    # Remove unwanted characters except for hyphens within words
    text = re.sub(r'(?<!\w)[.,;:_\'"\-\s]+(?!\w)', '', text)
    if ' ' in text:  # Skip if text contains multiple words
        return text

    words = word_tokenize(context)
    pos_tags = pos_tag(words)

    lemmatized_word = text  # Default to the original text
    for word, pos in pos_tags:
        if word.lower() == text.lower():
            wordnet_pos = get_wordnet_pos(pos)
            lemmatized_word = lemmatizer.lemmatize(word.lower(), pos=wordnet_pos)
            print(f"Word: {word}, POS: {pos}, Lemmatized: {lemmatized_word}")
            break

    return lemmatized_word

# Function to process a single note
def process_note(note, total_notes, index):
    note_id = note['noteId']
    text_field = note['fields']['Text']['value']
    context_field = note['fields']['Context']['value']

    cleaned_text = text_field.strip()

    # Skip processing if text field contains multiple words
    if ' ' in cleaned_text:
        print(f"{index + 1}/{total_notes} Skipping note {note_id}: Text is a phrase '{cleaned_text}'")
        return None

    lemmatized_text = clean_and_lemmatize(cleaned_text, context_field)

    if lemmatized_text != cleaned_text:
        print(f"{index + 1}/{total_notes} Updating note {note_id}: '{cleaned_text}' to '{lemmatized_text}'")
        update_note_field(note_id, 'Text', lemmatized_text)
        return {
            'note_id': note_id,
            'original_text': cleaned_text,
            'updated_text': lemmatized_text,
            'context': context_field,
            'status': 'updated'
        }
    else:
        print(f"{index + 1}/{total_notes} Note {note_id}: No update needed for '{cleaned_text}'")
        return {
            'note_id': note_id,
            'original_text': cleaned_text,
            'context': context_field,
            'status': 'not_updated'
        }

# Main function to process all notes
def main():
    note_ids = fetch_notes()
    notes = fetch_note_fields(note_ids)

    total_notes = len(notes)
    updated_notes = []
    not_updated_notes = []

    max_workers = 50  # Adjust this based on your system's capability
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_note = {executor.submit(process_note, note, total_notes, index): note for index, note in enumerate(notes)}

        for future in tqdm(concurrent.futures.as_completed(future_to_note), total=total_notes, desc="Processing notes"):
            try:
                result = future.result()
                if result:
                    if result['status'] == 'updated':
                        updated_notes.append(result)
                    else:
                        not_updated_notes.append(result)
            except Exception as e:
                print(f"Error processing note: {e}")

    # Print summary of updates
    if updated_notes:
        print("\nSummary of updates:")
        for note in updated_notes:
            print(f"Note {note['note_id']}: '{note['original_text']}' updated to '{note['updated_text']}'")

    # Export updated notes to Excel
    updated_df = pd.DataFrame(updated_notes, columns=['note_id', 'original_text', 'updated_text', 'context'])
    updated_df.to_excel('updated_notes.xlsx', index=False)

    # Export not updated notes to Excel
    not_updated_df = pd.DataFrame(not_updated_notes, columns=['note_id', 'original_text', 'context'])
    not_updated_df.to_excel('not_updated_notes.xlsx', index=False)

if __name__ == "__main__":
    main()
