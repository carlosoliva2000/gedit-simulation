import os
import json
import random
import subprocess
import string
import re
import argparse
import logging

from sys import exit
from typing import List, Optional
from logging.handlers import RotatingFileHandler

path = os.path.join(os.path.expanduser('~'), ".config", "gedit-simulation")
os.makedirs(path, exist_ok=True)

try:
    import pyautogui
    import pyperclip
except Exception as e:
    import traceback
    import datetime
    
    error_file = os.path.join(path, "error_gedit-simulation.log")
    with open(error_file, "a") as file:
        file.write("Date and time: \n")
        file.write(str(datetime.datetime.now()))
        file.write("\n\n")
        file.write("Error: \n")
        file.write(str(e))
        file.write("\n\n")
        file.write("Traceback: \n")
        file.write(str(traceback.format_exc()))
        file.write("\n\n")
        file.write("Environment variables: \n")
        file.write(str(os.environ))
        file.write("\n\n")


format_str = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(format_str)
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.WARNING)
logger.addHandler(console_handler)


def split_path_regex(path: str) -> List[str]:
    # Regex to split path elements such as "/" or "~"
    pattern = r'(~/|/|[^/]+)'
    return re.findall(pattern, path)


def load_words() -> List[str]:
    logger.debug("Loading words")
    try:
        # Get the first directory in /opt/ghosts if it exists
        json_path = os.path.join(
            '/opt/ghosts', 
            os.listdir('/opt/ghosts')[0], 
            'ghosts-client/config/dictionary.json'
        )

        with open(json_path, 'r', encoding='utf-8-sig') as file:
            words = json.load(file)
        logger.debug("Words loaded from remote dictionary")
    except Exception: # If not, use the local dictionary (FileNotFoundError)
        try:
            with open('dictionary.json', 'r', encoding='utf-8-sig') as file:
                words = json.load(file)
            logger.debug("Words loaded from local dictionary")
        except FileNotFoundError:
            logger.error("No dictionary found in the current directory (where is the dictionary.json file?)")
            exit(1)

    # Ensure all words are strings
    words = [str(word) for word in words]
    return words


def generate_paragraph(
        words: List[str],
        min_sentences: int,
        max_sentences: int,
        min_words: int,
        max_words: int
    ) -> str:
    num_sentences = random.randint(min_sentences, max_sentences)  # Number of sentences in the paragraph
    sentences = []
    
    for _ in range(num_sentences):
        num_words = random.randint(min_words, max_words)  # Number of words in the sentence
        sentence_words = random.choices(words, k=num_words)
        # print(sentence_words)
        sentence = ' '.join(sentence_words).capitalize() + '.'  # Join words and capitalize the first letter
        sentences.append(sentence)
    
    return ' '.join(sentences)


def generate_text(
        words: List[str],
        min_paragraphs: int,
        max_paragraphs: int,
        min_sentences: int,
        max_sentences: int,
        min_words: int,
        max_words: int
    ) -> str:
    num_paragraphs = random.randint(min_paragraphs, max_paragraphs)  # Number of paragraphs in the text
    paragraphs = [generate_paragraph(words, min_sentences, max_sentences, min_words, max_words) for _ in range(num_paragraphs)]
    return '\n\n'.join(paragraphs)  # Join paragraphs with two newlines


def generate_filename(
        min_filename_length: int,
        max_filename_length: int
    ) -> str:
    length = random.randint(min_filename_length, max_filename_length)  # Length of the filename
    characters = string.ascii_letters + string.digits  # Mix of letters (upper and lower case) and digits
    filename = ''.join(random.choice(characters) for _ in range(length)) + '.txt'
    return filename


def save_file(path: str, filename: str, interval: float):
    path = os.path.join(path, filename)

    pyautogui.hotkey('ctrl', 'shift' , 's')
    pyautogui.sleep(1)  # Wait for the save dialog to appear
    parts = split_path_regex(path)
    logger.debug(f"Split path: {parts}")

    for part in parts:
        # Fix to writing special characters
        if '/' in part or '~' in part:
            pyperclip.copy(part)
            pyautogui.sleep(0.05)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.sleep(0.05)
        else:
            pyautogui.write(part, interval)

    pyautogui.sleep(1)  # Wait for the save dialog to appear
    pyautogui.press('enter')
    pyautogui.sleep(2)



def random_execution(args: argparse.Namespace, subparsers: argparse._SubParsersAction) -> argparse.Namespace:
    # Check if should execute the command
    if random.random() > args.execution / 100:
        logger.info("Due to the probabilities, the command will not be executed.")
        print("Due to the probabilities, the command will not be executed.")
        exit(0)

    # Check if the probabilities sum to 100
    if args.create + args.edit + args.view + args.delete != 100:
        logger.error("The sum of the probabilities of the verbs (create, edit, view, delete) must be 100.")
        exit(1)

    verbs = ['create', 'edit', 'view', 'delete']
    probabilities = [
        args.create / 100,
        args.edit / 100,
        args.view / 100,
        args.delete / 100
    ]
    
    # Choose a random command based on the probabilities
    chosen_command = random.choices(verbs, probabilities)[0]
    
    # Get and call the chosen command parser
    # command_parser = parser._subparsers._parser_map[chosen_command]
    command_parser: argparse.ArgumentParser = subparsers.choices[chosen_command]
    # command_args, remaining_args = command_parser.parse_known_args(args.input, args.output)
    command_args = command_parser.parse_known_args(namespace=args)[0]

    command_args.command = chosen_command
    logger.debug(f'Chosen command "{chosen_command}" with args: {command_args}')

    return command_args


def delete_process(input_dir: str):
    input_dir = os.path.expanduser(input_dir)
    if input_dir.lower().endswith('.txt') or input_dir.lower().endswith('.md'):
        logger.debug(f"Input directory is a file, using it as a filename")
        file_to_delete = input_dir
    else:
        # Choose a .txt random file to delete
        # TODO: add more types or use an argument to determine what to delete
        files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
        if not files:
            logger.debug(f"No files found in {input_dir}")
            return
        
        file_to_delete = random.choice(files)
    logger.debug(f"Deleting {file_to_delete}")
    os.remove(os.path.join(input_dir, file_to_delete))


def view_process(input_dir: str, min_time: int, max_time: int, fixed_time: Optional[int] = None):
    input_dir = os.path.expanduser(input_dir)
    if input_dir.lower().endswith('.txt') or input_dir.lower().endswith('.md'):
        logger.debug(f"Input directory is a file, using it as a filename")
        file_to_view = input_dir
    else:
        logger.debug(f"Input directory is a directory, choosing a random file")
        # Choose a .txt random file to view
        files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
        if not files:
            logger.debug(f"No files found in {input_dir}")
            return

        file_to_view = random.choice(files)
    
    if fixed_time:
        time = fixed_time
    else:
        time = random.randint(min_time, max_time)
    logger.debug(f"Viewing {file_to_view} for {time} seconds")

    # Open gedit
    subprocess.Popen(['gedit', os.path.join(input_dir, file_to_view)])

    # Ensure the focus is on the gedit window
    pyautogui.sleep(3)
    os.system("wmctrl -xa gedit.Gedit")

    # Wait for the time
    pyautogui.sleep(time)

    # Ensure the focus is on the gedit window again
    os.system("wmctrl -xa gedit.Gedit")
    pyautogui.sleep(1)
    logger.debug("Closing gedit")

    # Close gedit
    pyautogui.hotkey('alt', 'f4')


def edit_process(
        input_dir: str, 
        min_paragraphs: int, 
        max_paragraphs: int, 
        min_sentences: int, 
        max_sentences: int, 
        min_words: int, 
        max_words: int,
        interval: float
    ):
    input_dir = os.path.expanduser(input_dir)
    if input_dir.lower().endswith('.txt') or input_dir.lower().endswith('.md'):
        logger.debug(f"Input directory is a file, using it as a filename")
        file_to_edit = input_dir
    else:
        logger.debug(f"Input directory is a directory, choosing a random file")
        # Choose a .txt random file to edit
        files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
        if not files:
            logger.debug(f"No files found in {input_dir}")
            return
        
        file_to_edit = random.choice(files)
    logger.debug(f"Editing {file_to_edit}")

    # Load the words
    words = load_words()

    # Generate the text
    generated_text = generate_text(words, min_paragraphs, max_paragraphs, min_sentences, max_sentences, min_words, max_words)

    # Open gedit
    subprocess.Popen(['gedit', os.path.join(input_dir, file_to_edit)])

    # Ensure the focus is on the gedit window
    pyautogui.sleep(3)
    os.system("wmctrl -xa gedit.Gedit")

    # Go to the end of the file
    pyautogui.hotkey('ctrl', 'end')
    pyautogui.write('\n\n', interval=interval)

    # Write the generated text
    pyautogui.sleep(3)
    pyautogui.write(generated_text, interval=interval)
    pyautogui.sleep(1)

    # Save the file
    pyautogui.hotkey('ctrl', 's')
    pyautogui.sleep(2)

    # Close gedit
    pyautogui.hotkey('alt', 'f4')


def create_process(
        output_dir: str,
        min_paragraphs: int,
        max_paragraphs: int,
        min_sentences: int,
        max_sentences: int,
        min_words: int,
        max_words: int,
        min_filename_length: int,
        max_filename_length: int,
        interval: float
    ):
    # Load the words
    words = load_words()

    # Generate the text
    generated_text = generate_text(words, min_paragraphs, max_paragraphs, min_sentences, max_sentences, min_words, max_words)

    # Generate the filename
    random_filename = generate_filename(min_filename_length, max_filename_length)
    logger.debug(f"Generating {random_filename}")

    # Open gedit
    output_dir = os.path.expanduser(output_dir)
    if output_dir.lower().endswith('.txt') or output_dir.lower().endswith('.md'):
        logger.debug(f"Output directory is a file, using it as a filename")
        output_file = output_dir
    else:
        logger.debug(f"Output directory is a directory, appending the filename")
        output_file = os.path.join(output_dir, random_filename)
    logger.info(f"Creating in {output_file}")
    subprocess.Popen(['gedit', output_file])
    # subprocess.run(['gedit', output_file])
    # os.system("gedit &")

    # Ensure the focus is on the gedit window
    pyautogui.sleep(3)
    os.system("wmctrl -xa gedit.Gedit")

    # Write the generated text
    pyautogui.write(generated_text, interval=interval)
    pyautogui.sleep(1)

    # Save the file
    # save_file(output_dir, random_filename, interval)  # FIXME: Not working
    pyautogui.hotkey('ctrl', 's')

    # Close gedit
    # os.system("wmctrl -xa gedit.Gedit")
    pyautogui.sleep(1)
    pyautogui.hotkey('alt', 'f4')


def main():
    parser = argparse.ArgumentParser(
        prog='gedit-simulation',
        description='Simulate activity in gedit, writing, editing, viewing and deleting files.',
    )
    # parser.add_argument('args', nargs=argparse.REMAINDER)


    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True, help='Command to execute')

    # Subcommand create
    create_parser = subparsers.add_parser('create', help='Create a random text file')
    create_parser.add_argument('--min-paragraphs', '-p', type=int, default=2, help='Minimum number of paragraphs to generate.')
    create_parser.add_argument('--max-paragraphs', '-P', type=int, default=4, help='Maximum number of paragraphs to generate.')
    create_parser.add_argument('--min-sentences', '-s', type=int, default=2, help='Minimum number of sentences per paragraph.')
    create_parser.add_argument('--max-sentences', '-S', type=int, default=10, help='Maximum number of sentences per paragraph.')
    create_parser.add_argument('--min-words', '-w', type=int, default=4, help='Minimum number of words per sentence.')
    create_parser.add_argument('--max-words', '-W', type=int, default=15, help='Maximum number of words per sentence.')
    create_parser.add_argument('--min-filename-length', type=int, default=4, help='Minimum length of the generated filename.')
    create_parser.add_argument('--max-filename-length', type=int, default=8, help='Maximum length of the generated filename.')
    create_parser.add_argument('--interval-between-keystrokes', type=float, default=0.025, help='Interval (in seconds) between keystrokes when writing the generated text.')
    create_parser.add_argument('--interval-between-keystrokes-filepath', type=float, default=0.025, help='Interval (in seconds) between keystrokes when writing the filepath.')
    create_parser.add_argument('--text-generation', type=str, choices=['random'], default='random', help='Text generation method.')
    create_parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    create_parser.add_argument('--log', type=str, help='Log directory to save log files to. If it does not exist, it will be created.', default=path)
    create_parser.add_argument('--output', '-O', type=str, required=True, help='Output directory to save files to. If not a directory, it will be used as a filename.')

    # Subcommand view
    view_parser = subparsers.add_parser('view', help='View the content of a file')
    view_parser.add_argument('--min-time', type=int, default=30, help='Minimum time (in seconds) to view the file.')
    view_parser.add_argument('--max-time', type=int, default=30, help='Maximum time (in seconds) to view the file.')
    view_parser.add_argument('--time', '-t', type=int, help='Fixed time (in seconds) to view the file. Overrides --min-time and --max-time.')
    view_parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    view_parser.add_argument('--log', type=str, help='Log directory to save log files to. If it does not exist, it will be created.', default=path)
    view_parser.add_argument('--input', '-I', type=str, required=True, help='Input directory to read files from. If it is a file, it will be used as a filename.')

    # Subcommand edit
    edit_parser = subparsers.add_parser('edit', help='Edit an existing file and save changes')
    edit_parser.add_argument('--min-paragraphs', type=int, default=2, help='Minimum number of paragraphs to generate.')
    edit_parser.add_argument('--max-paragraphs', type=int, default=4, help='Maximum number of paragraphs to generate.')
    edit_parser.add_argument('--min-sentences', type=int, default=2, help='Minimum number of sentences per paragraph.')
    edit_parser.add_argument('--max-sentences', type=int, default=10, help='Maximum number of sentences per paragraph.')
    edit_parser.add_argument('--min-words', type=int, default=4, help='Minimum number of words per sentence.')
    edit_parser.add_argument('--max-words', type=int, default=15, help='Maximum number of words per sentence.')
    edit_parser.add_argument('--interval-between-keystrokes', type=float, default=0.025, help='Interval (in seconds) between keystrokes when writing the generated text.')
    edit_parser.add_argument('--text-generation', type=str, choices=['random'], default='random', help='Text generation method.')
    edit_parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    edit_parser.add_argument('--log', type=str, help='Log directory to save log files to. If it does not exist, it will be created.', default=path)
    edit_parser.add_argument('--input', '-I', type=str, required=True, help='Input directory to read files from. If it is a file, it will be used as a filename.')
    # edit_parser.add_argument('--output', '-O', type=str, required=True, help='Output directory to save files to. If not a directory, it will be used as a filename.')

    # Subcommand delete
    delete_parser = subparsers.add_parser('delete', help='Delete a file')
    delete_parser.add_argument('--log', type=str, help='Log directory to save log files to. If it does not exist, it will be created.', default=path)
    delete_parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    delete_parser.add_argument('--input', '-I', type=str, required=True, help='Input directory to read files from. If it is a file, it will be used as a filename.')

    # Subcommand random
    random_parser = subparsers.add_parser('random', help='Execute a random command based on provided probabilities')
    random_parser.add_argument('--execution', type=int, default=100, help='Probability (in %%) of execution of any verb.')
    random_parser.add_argument('--create', '-c', type=int, default=50, help='Probability (in %%) of executing "create".')
    random_parser.add_argument('--edit', '-e', type=int, default=20, help='Probability (in %%) of executing "edit".')
    random_parser.add_argument('--view', '-v', type=int, default=20, help='Probability (in %%) of executing "view".')
    random_parser.add_argument('--delete', '-d', type=int, default=10, help='Probability (in %%) of executing "delete".')
    random_parser.add_argument('--log', type=str, help='Log directory to save log files to. If it does not exist, it will be created.', default=path)
    random_parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    random_parser.add_argument('--input', '-I', type=str, required=True, help='Input directory to read files from.', )
    random_parser.add_argument('--output', '-O', type=str, required=True, help='Output directory to save files to.')

    # TODO: try to use nargs=argparse.REMAINDER or something similar to capture the remaining arguments without specifying them here again
    random_parser.add_argument('--min-paragraphs', '-p', type=int, default=2, help=argparse.SUPPRESS)
    random_parser.add_argument('--max-paragraphs', '-P', type=int, default=4, help=argparse.SUPPRESS)
    random_parser.add_argument('--min-sentences', '-s', type=int, default=2, help=argparse.SUPPRESS)
    random_parser.add_argument('--max-sentences', '-S', type=int, default=10, help=argparse.SUPPRESS)
    random_parser.add_argument('--min-words', '-w', type=int, default=4, help=argparse.SUPPRESS)
    random_parser.add_argument('--max-words', '-W', type=int, default=15, help=argparse.SUPPRESS)
    random_parser.add_argument('--min-filename-length', type=int, default=4, help=argparse.SUPPRESS)
    random_parser.add_argument('--max-filename-length', type=int, default=8, help=argparse.SUPPRESS)
    random_parser.add_argument('--interval-between-keystrokes', type=float, default=0.025, help=argparse.SUPPRESS)
    random_parser.add_argument('--interval-between-keystrokes-filepath', type=float, default=0.025, help=argparse.SUPPRESS)
    random_parser.add_argument('--text-generation', type=str, choices=['random'], default='random', help=argparse.SUPPRESS)
    random_parser.add_argument('--min-time', type=int, default=30, help=argparse.SUPPRESS)
    random_parser.add_argument('--max-time', type=int, default=30, help=argparse.SUPPRESS)
    random_parser.add_argument('--time', '-t', type=int, default=None, help=argparse.SUPPRESS)

    random_parser.add_argument('remaining_args', nargs=argparse.REMAINDER, help='Remaining arguments for the selected command (see help for each command).')

    # Parse arguments
    # args = parser.parse_args()
    args, unknown = parser.parse_known_args()
    if unknown:
        logger.warning(f"Unknown arguments ignored: {unknown}")

    file_handler = RotatingFileHandler(
        os.path.join(os.path.expanduser(args.log), 'gedit-simulation.log'),
        maxBytes=1024*1024, 
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    if args.debug:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info("Starting gedit-simulation")

    # In case of random command, choose a random command based on the probabilities
    if args.command == 'random':
        args = random_execution(args, subparsers)
    else:
        logger.debug(f'Chosen command "{args.command}" with args: {args}')

    
    # Sanitize the input directory (expand user)
    if args.command in ['view', 'edit', 'delete']:
        args.input = os.path.expanduser(args.input)
    
    if args.command == 'create':
        create_process(
            args.output,
            args.min_paragraphs,
            args.max_paragraphs,
            args.min_sentences,
            args.max_sentences,
            args.min_words,
            args.max_words,
            args.min_filename_length,
            args.max_filename_length,
            args.interval_between_keystrokes
        )
    elif args.command == 'edit':
        edit_process(
            args.input,
            args.min_paragraphs,
            args.max_paragraphs,
            args.min_sentences,
            args.max_sentences,
            args.min_words,
            args.max_words,
            args.interval_between_keystrokes
        )
    elif args.command == 'view':
        view_process(args.input, args.min_time, args.max_time, args.time)
    elif args.command == 'delete':
        delete_process(args.input)
    else:
        logger.error(f'Unknown command "{args.command}". Exiting.')
        exit(1)
    logger.info("Finishing gedit-simulation")


if __name__ == '__main__':
    main()

# except Exception as e:
#     import traceback
#     import datetime
    
#     with open("/home/usuario/error_gedit-simulator.log", "a") as file:
#         file.write("Date and time: \n")
#         file.write(str(datetime.datetime.now()))
#         file.write("\n\n")
#         file.write("Error: \n")
#         file.write(str(e))
#         file.write("\n\n")
#         file.write("Traceback: \n")
#         file.write(str(traceback.format_exc()))
#         file.write("\n\n")
#         file.write("Environment variables: \n")
#         file.write(str(os.environ))
#         file.write("\n\n")
