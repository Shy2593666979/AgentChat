# encoding=utf-8
import json
import logging


def load_file_to_obj(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading scene prompts: {e}")
        return {}
