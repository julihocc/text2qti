# -*- coding: utf-8 -*-
#
# Copyright (c) 2026, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import pathlib
import platform
import shutil
import subprocess

from .err import Text2qtiError
from .export import quiz_to_pandoc
from .qti import QTI
from .quiz import Quiz


def read_quiz_text(path: pathlib.Path) -> str:
    '''
    Read a quiz file as UTF-8, accepting a leading BOM.
    '''
    try:
        return path.read_text(encoding='utf-8-sig')
    except FileNotFoundError:
        raise Text2qtiError(f'File "{path}" does not exist')
    except PermissionError as e:
        raise Text2qtiError(f'File "{path}" cannot be read due to permission error:\n{e}')
    except UnicodeDecodeError as e:
        raise Text2qtiError(f'File "{path}" is not encoded in valid UTF-8:\n{e}')


def write_qti(quiz: Quiz, path: pathlib.Path) -> None:
    '''
    Write a quiz to a QTI zip file.
    '''
    QTI(quiz).save(path)


def export_solutions(quiz: Quiz, paths: list[pathlib.Path]) -> None:
    '''
    Write solutions for a quiz to one or more .md, .markdown, .pdf, or .html files.

    PDF export requires Pandoc and pdflatex. HTML export requires Pandoc.
    The solutions text is generated once and reused for every path.
    '''
    solutions_text = quiz_to_pandoc(quiz, solutions=True)
    for solutions_path in paths:
        if solutions_path.suffix.lower() == '.pdf':
            if not shutil.which('pandoc'):
                raise Text2qtiError('Exporting solutions in PDF format requires Pandoc (https://pandoc.org/)')
            if not shutil.which('pdflatex'):
                raise Text2qtiError('Exporting solutions in PDF format requires LaTeX (https://www.tug.org/texlive/ or https://miktex.org/)')
            if platform.system() == 'Windows':
                cmd = [shutil.which('pandoc'), '-f', 'markdown', '-o', str(solutions_path)]
            else:
                cmd = ['pandoc', '-f', 'markdown', '-o', str(solutions_path)]
            try:
                subprocess.run(
                    cmd,
                    input=solutions_text,
                    capture_output=True,
                    check=True,
                    encoding='utf8'
                )
            except subprocess.CalledProcessError as e:
                raise Text2qtiError(f'Pandoc failed:\n{"-"*78}\n{e}\n{"-"*78}')
        elif solutions_path.suffix.lower() == '.html':
            if not shutil.which('pandoc'):
                raise Text2qtiError('Exporting solutions in HTML format requires Pandoc (https://pandoc.org/)')
            if platform.system() == 'Windows':
                cmd = [shutil.which('pandoc'), '-f', 'markdown', '-o', str(solutions_path), '--mathjax', '-s']
            else:
                cmd = ['pandoc', '-f', 'markdown', '-o', str(solutions_path), '--mathjax', '-s']
            try:
                subprocess.run(
                    cmd,
                    input=solutions_text,
                    capture_output=True,
                    check=True,
                    encoding='utf8'
                )
            except subprocess.CalledProcessError as e:
                raise Text2qtiError(f'Pandoc failed:\n{"-"*78}\n{e}\n{"-"*78}')
        elif solutions_path.suffix.lower() in ('.md', '.markdown'):
            solutions_path.write_text(solutions_text, encoding='utf8')
        else:
            raise ValueError
