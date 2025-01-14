import json
import os
import random
import pyautogui
import subprocess
import string

import pyperclip
import re

from typing import List


def split_path_regex(path: str) -> List[str]:
    # Regex to split path elements such as "/" or "~"
    pattern = r'(~/|/|[^/]+)'
    return re.findall(pattern, path)


def load_words() -> List[str]:
    # Get the first directory in /opt/ghosts if it exists
    json_path = os.path.join(
        '/opt/ghosts', 
        os.listdir('/opt/ghosts')[0], 
        'ghosts-client/config/dictionary.json'
    )

    try:
        with open(json_path, 'r', encoding='utf-8-sig') as file:
            words = json.load(file)
    except FileNotFoundError: # If not, use the local dictionary
        with open('dictionary.json', 'r', encoding='utf-8-sig') as file:
            words = json.load(file)

    # Ensure all words are strings
    words = [str(word) for word in words]
    return words


def generate_paragraph(words: List[str]) -> str:
    num_sentences = random.randint(2, 10)  # Number of sentences in the paragraph
    sentences = []
    
    for _ in range(num_sentences):
        num_words = random.randint(4, 15)  # Number of words in the sentence
        sentence_words = random.choices(words, k=num_words)
        # print(sentence_words)
        sentence = ' '.join(sentence_words).capitalize() + '.'  # Join words and capitalize the first letter
        sentences.append(sentence)
    
    return ' '.join(sentences)


def generate_text(words: List[str]) -> str:
    num_paragraphs = random.randint(2, 4)  # Number of paragraphs in the text
    paragraphs = [generate_paragraph(words) for _ in range(num_paragraphs)]
    return '\n\n'.join(paragraphs)  # Join paragraphs with two newlines


def generate_filename() -> str:
    length = random.randint(4, 8)  # Length of the filename
    characters = string.ascii_letters + string.digits  # Mix of letters (upper and lower case) and digits
    filename = ''.join(random.choice(characters) for _ in range(length)) + '.txt'
    return filename


def save_file(path: str, filename: str):
    path = os.path.join(path, filename)

    pyautogui.hotkey('ctrl', 's')
    pyautogui.sleep(1)  # Wait for the save dialog to appear
    parts = split_path_regex(path)
    print(parts)

    for part in parts:
        # Fix to writing special characters
        if '/' in part or '~' in part:
            pyperclip.copy(part)
            pyautogui.sleep(0.05)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.sleep(0.05)
        else:
            pyautogui.write(part, interval=0.025)

    pyautogui.sleep(1)  # Wait for the save dialog to appear
    pyautogui.press('enter')
    pyautogui.sleep(2)


def main():
    # Load the words
    words = load_words()

    # Generate the text
    generated_text = generate_text(words)

    # Generate the filename
    random_filename = generate_filename()
    print(f"Generando {random_filename}")

    # Open gedit
    subprocess.Popen(['gedit'])

    # Ensure the focus is on the gedit window
    pyautogui.sleep(3)
    os.system("wmctrl -xa gedit.Gedit")
    # pyautogui.click(pyautogui.size().width // 2, pyautogui.size().height // 2)

    # Write the generated text
    pyautogui.write(generated_text, interval=0.025)
    pyautogui.sleep(1)

    # Save the file
    path = "~/Escritorio"
    save_file(path, random_filename)

    # Close gedit
    pyautogui.hotkey('alt', 'f4')


if __name__ == '__main__':
    main()
