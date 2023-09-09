import os

def Settings( **kwargs ):
    return {
            'interpreter_path': os.path.join(
            os.path.dirname(__file__), 'venv/bin/python')
            }
