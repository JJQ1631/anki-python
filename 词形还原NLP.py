import json
import requests
import re
from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from concurrent.futures import ThreadPoolExecutor, as_completed

# 初始化NLTK的WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

ANKI_CONNECT_URL = 'http://localhost:8765'

def invoke(action, **params):
    response = requests.post(ANKI_CONNECT_URL, json={'action': action, 'params': params, 'version': 6})
    return response.json()

def get_notes(deck_name):
    query = f'deck:"{deck_name}"'
    response = invoke('findNotes', query=query)
    return response['result']

def get_note_info(note_ids):
    response = invoke('notesInfo', notes=note_ids)
    return response['result']

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def lemmatize_sentence(sentence):
    tokens = word_tokenize(sentence)
    pos_tags = pos_tag(tokens)
    lemmas = []
    for token, tag in pos_tags:
        wn_tag = get_wordnet_pos(tag)
        if wn_tag is None:
            lemma = lemmatizer.lemmatize(token)
        else:
            lemma = lemmatizer.lemmatize(token, pos=wn_tag)
        lemmas.append((token, tag, lemma))
    return lemmas

def update_note_field(note_id, field_name, value):
    invoke('updateNoteFields', note={'id': note_id, 'fields': {field_name: value}})

def clean_text_field(text):
    symbols_to_remove = re.compile(r'[^\w\s\-]')
    cleaned_text = re.sub(symbols_to_remove, '', text)
    return cleaned_text

def process_note(note):
    try:
        original_text = note['fields']['Text']['value']
        if not isinstance(original_text, str):
            print(f"Skipped note {note['noteId']} because Text field is not a string.")
            return

        cleaned_text = clean_text_field(original_text)

        context_sentence = note['fields']['Context']['value']
        cleaned_context_sentence = clean_text_field(context_sentence)
        lemmatized_info = lemmatize_sentence(cleaned_context_sentence)
        feedback = []
        new_text = []

        for token, tag, lemma in lemmatized_info:
            feedback.append(f"Token: {token}, POS: {tag}, Lemma: {lemma}")
            if token.lower() == cleaned_text.lower():
                new_text.append(lemma)

        if new_text:
            new_text_str = " ".join(new_text)
            if new_text_str.lower() != cleaned_text.lower():
                print(f"Original Text: {cleaned_text} => Updated Text: {new_text_str}")
                update_note_field(note['noteId'], 'Text', new_text_str)
        else:
            print(f"No lemmatization needed for Text: {cleaned_text}")

        print("\n".join(feedback))
        print("-" * 40)

    except Exception as e:
        print(f"Error processing note {note['noteId']}: {str(e)}")

def main():
    deck_name = "Saladict"
    notes = get_notes(deck_name)
    notes_info = get_note_info(notes)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_note, note) for note in notes_info]
        for future in as_completed(futures):
            future.result()

    print("All notes processed successfully.")

if __name__ == "__main__":
    main()
