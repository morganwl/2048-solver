import os
import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

short_description = ('2048 AI solver, with an ncurses interface.')

setuptools.setup(
        name='2048-solver-morgan',
        version='0.0.1',
        author='Morgan Wajda-Levie',
        author_email='morgan.wajdalevie@gmail.com',
        description=short_description,
        packages=setuptools.find_packages(),
        install_requires=(
            'numpy',
            ,)
        )
