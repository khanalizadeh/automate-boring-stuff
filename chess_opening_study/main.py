import io
import requests
import chess.pgn
import chess.svg
from cairosvg import svg2png
import random
import argparse
import os
import json
import genanki

CHESS_OPENING_MODEL_ID = 1657392315 # This should not change, so the notes will all have the same type
DEFAULT_CSS = '.card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;}'


def get_auth_token():
    try:
        with open('auth.txt', 'r') as f:
            auth_token = f.read().strip()
            return auth_token
    except FileNotFoundError:
        return ''

def export_study_pgn(study_id, auth_token = '', clocks=False, comments=True, variations=False, orientation=True):
    # exports all chapters in a lichess study as a string with pgn format
    url = f'https://lichess.org/api/study/{study_id}.pgn'
    headers = {
        "Authorization": f"Bearer {auth_token}",
    }
    params = {
        "clocks": "true" if clocks else "false",
        "comments": "true" if comments else "false",
        "variations": "true" if variations else "false",
        "orientation": "true" if orientation else "false"
    }
    response = requests.get(url=url, headers=headers, params=params)
    return response.text

def get_chapters_from_pgn(pgn):
    # returns a list of Game objects, from the PGN string
    chapters = []
    games = io.StringIO(pgn)
    chapter = chess.pgn.read_game(games)

    while chapter is not None:
        chapters.append(chapter)
        chapter = chess.pgn.read_game(games)

    return chapters

def generate_diagram(board, last_move, filename):
    diagram_svg = chess.svg.board(board=board, lastmove=last_move)
    png_filename = filename
    svg2png(bytestring=diagram_svg, write_to=png_filename)
    return png_filename


def get_san_from_movelist(movelist):
    board = chess.Board()
    return board.variation_san(movelist)

def generate_filename(fen):
    modified_fen = fen.replace('/', '\\')
    return f"diagram - after {modified_fen}.png"

def get_notes_from_chapter(chapter):
    # returns a list of dictionaries
    notes = []
    game = chapter.game()
    board = game.board()
    orientation = chess.WHITE if game.headers['Orientation'] == 'white' else chess.BLACK
    chapter_title = game.headers['Event']
    node = game.game()
    movelist = []
    while node is not None:
        if node.move:
            movelist.append(node.move)
            board.push(node.move)
        movelist_san = get_san_from_movelist(movelist)
        last_move = node.move
        next_move = node.next().move if node.next() else None
        movelist_san_next = get_san_from_movelist(movelist + [next_move]) if next_move else None
        if next_move:
            board_next = board.copy()
            board_next.push(next_move)
        else:
            board_next = None
        fen = board.fen()
        fen_next = board_next.fen() if board_next else ''
        fn_before = generate_filename(fen)
        fn_after = generate_filename(fen_next) if fen_next else ''
        if orientation == board.turn:
            note = {
                'movelist': movelist_san,
                'fen':fen,
                'diagram_before': f"<img src=\"{generate_diagram(board=board, last_move = last_move, filename=fn_before)}\">",
                'next_move': board.san(node.next().move) if node.next() else '',
                'diagram_after': f"<img src=\"{generate_diagram(board=board_next, last_move=next_move, filename=fn_after)}\">" if board_next else '',
                'comment_before': node.comment,
                'comment_after': node.next().comment if node.next() else '',
                'diagram_before_fn': fn_before,
                'diagram_after_fn': fn_after,
                'chapter_title': chapter_title,
                'study_id': study_id
            }
            notes.append(note)
        node = node.next()
    return notes

def get_notes_from_all_chapters(chapters):
    # get notes from unique positions
    notes = []
    media_files = []
    seen_fen_values = set()
    for chapter in chapters:
        for note in get_notes_from_chapter(chapter):
            fen_value = note.get('fen')
            if fen_value not in seen_fen_values:
                seen_fen_values.add(fen_value)
                notes.append(note)
                media_files.append(note.get('diagram_before_fn'))
                media_files.append(note.get('diagram_after_fn'))
    return notes, media_files

def get_deck_id(study_id):
    # get deck IDs from previous studies, or make a new one
    studies = []
    try:
        with open('existing_studies.json', 'r') as f:
            studies = json.loads(f.read())
        
        for study in studies:
            if study.get('study_id') == study_id:
                return study.get('deck_id')
            
    except FileNotFoundError:
        pass
    
    deck_id = random.randrange(1 << 30, 1 << 31)

    studies.append({'study_id': study_id, 'deck_id': deck_id})

    with open('existing_studies.json', 'w') as f:
        json.dump(studies, f)

    return deck_id





parser = argparse.ArgumentParser()
parser.add_argument("study_id", help="ID of the study", type=str)
args = parser.parse_args()
study_id = args.study_id

pgn = export_study_pgn(study_id=study_id, auth_token=get_auth_token())
chapters = get_chapters_from_pgn(pgn=pgn)
notes, media_files = get_notes_from_all_chapters(chapters=chapters)

chess_model = genanki.Model(
    CHESS_OPENING_MODEL_ID,
    'Chess Opening',
    fields=[
        {'name': 'FEN'},
        {'name': 'Diagram'},
        {'name': 'MoveList'},
        {'name': 'Comment'},
        {'name': 'SolutionDiagram'},
        {'name': 'Solution'},
        {'name': 'Chapter Title'},
        {'name': 'Study ID'}
    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt':'{{Diagram}}<br>{{MoveList}}',
            'afmt':'{{SolutionDiagram}}<br>{{Solution}}<br>{{Comment}}'
        }
    ],
    css = DEFAULT_CSS
)


deck = genanki.Deck(get_deck_id(study_id), study_id)

for note in notes:
    anki_note = genanki.Note(model=chess_model, fields=[
        note.get('fen'),
        note.get('diagram_before'),
        note.get('movelist'),
        note.get('comment_after'),
        note.get('diagram_after'),
        note.get('next_move'),
        note.get('chapter_title'),
        note.get('study_id')
    ])
    deck.add_note(anki_note)

package = genanki.Package(deck)
package.media_files = media_files

home_directory = os.path.expanduser('~')
folder_path = os.path.join(home_directory, 'Anki Packages')

try:
    package.write_to_file(os.path.join(folder_path, f'{study_id}.apkg'))
except FileNotFoundError:
    os.makedirs(folder_path)

for file in media_files:
    # clean media files
    os.remove(file)

