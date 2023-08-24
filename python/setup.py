import os
import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

short_description = ('2048 AI solver, with an ncurses interface.')
scripts = [os.path.join('twentysolver', 'play.py')]

setuptools.setup(
        name='twenty-solver-morgan',
        version='0.0.1',
        author='Morgan Wajda-Levie',
        author_email='morgan.wajdalevie@gmail.com',
        description=short_description,
        packages=setuptools.find_packages(),
        install_requires=(
            'numpy',
            ),
        scripts = scripts,
        )
