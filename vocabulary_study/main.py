from gtts import gTTS
import os
import genanki
import csv

FRENCH_VOCABULARY_MODEL_ID = 1658392318 # This should not change, so the notes will all have the same type
FRENCH_VOCABULARY_DECK_ID = 1658132398 # This should not change, so the notes will all end up in the same deck
DEFAULT_CSS = '.card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;}'

def download_pronunciation(word, lang='fr'):
    tts = gTTS(text=word, lang=lang)
    fn = f'{word}.mp3'
    tts.save(fn)
    return fn

def get_notes_from_csv(csv_file):
    notes = []
    media_files = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            media_file = download_pronunciation(row['french'])
            media_files.append(media_file)
            notes.append({
                'french': row['french'],
                'english': row['english'],
                'pronunciation': f"[sound:{media_file}]",
            })

    return notes, media_files

vocabulary_model = genanki.Model(
    FRENCH_VOCABULARY_MODEL_ID,
    'French Vocabulary',
    fields=[
        {'name': 'French'},
        {'name': 'English'},
        {'name': 'Pronunciation'},
        {'name': 'Comment'}
    ],
    templates=[
        {
            'name': 'FR -> EN',
            'qfmt':'{{French}}<br>{{Pronunciation}}',
            'afmt':'{{FrontSide}}<hr id="answer">{{English}}<br><br>{{Comment}}'
        },
        {
            'name': 'EN -> FR',
            'qfmt':'{{English}}',
            'afmt':'{{FrontSide}}<hr id="answer">{{French}}<br>{{Pronunciation}}<br><br>{{Comment}}'
        }
    ],
    css=DEFAULT_CSS
)

deck = genanki.Deck(FRENCH_VOCABULARY_DECK_ID, 'French Vocabulary')

notes, media_files = get_notes_from_csv('words.csv')

for note in notes:
    anki_note = genanki.Note(model=vocabulary_model, fields=[
        note.get('french'),
        note.get('english'),
        note.get('pronunciation'),
        ''
        ])
    deck.add_note(anki_note)

package = genanki.Package(deck)
package.media_files = media_files

home_directory = os.path.expanduser('~')
folder_path = os.path.join(home_directory, 'Anki Packages')

try:
    package.write_to_file(os.path.join(folder_path, 'fr_vocabulary.apkg'))
except FileNotFoundError:
    os.makedirs(folder_path)

for file in media_files:
    # clean media files
    os.remove(file)
