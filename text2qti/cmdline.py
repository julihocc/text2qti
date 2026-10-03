# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import argparse
import pathlib
import sys
from .version import __version__ as version
from .err import Text2qtiError
from .config import Config
from .quiz import Quiz
from .convert import export_solutions, read_quiz_text, write_qti
from .preview import quiz_to_preview_json



def main():
    '''
    text2qti executable main function.
    '''
    parser = argparse.ArgumentParser(prog='text2qti')
    parser.set_defaults(func=lambda x: parser.print_help())
    parser.add_argument('--version', action='version', version=f'text2qti {version}')
    parser.add_argument('--latex-render-url',
                        help='URL for rendering LaTeX equations')
    parser.add_argument('--run-code-blocks', action='store_const', const=True,
                        help='Allow special code blocks to be executed and insert their output (off by default for security)')
    parser.add_argument('--pandoc-mathml', action='store_const', const=True,
                        help='Convert LaTeX math to MathML using Pandoc (this will create a cache file "_text2qti_cache.zip" in the quiz file directory)')
    soln_group = parser.add_mutually_exclusive_group()
    soln_group.add_argument('--solutions', action='append', metavar='SOLUTIONS_FILE',
                            help='Save solutions in Pandoc Markdown (.md), PDF (.pdf), or HTML (.html) format, and also create a QTI file. '
                                 'Can be used multiple times to export multiple formats. '
                                 'Pandoc Markdown output is only suitable for use with LaTeX or HTML; PDF output requires Pandoc plus LaTeX.')
    soln_group.add_argument('--only-solutions', action='append', metavar='SOLUTIONS_FILE',
                            help='Save solutions in Pandoc Markdown (.md), PDF (.pdf), or HTML (.html) format, but do not create a QTI file. '
                                 'Can be used multiple times to export multiple formats. '
                                 'Pandoc Markdown output is only suitable for use with LaTeX or HTML; PDF output requires Pandoc plus LaTeX. '
                                 'With this option, solutions and QTI may differ if executable code blocks generate problems using random numbers. '
                                 'Consider creating solutions and QTI together, or setting a seed for the random number generator so it is reproducible.')
    parser.add_argument('--preview', action='store_const', const=True,
                        help='Write quiz to STDOUT in JSON format for a compatible previewer. No QTI is created.')
    parser.add_argument('file',
                        help='File to convert from text to QTI')
    args = parser.parse_args()
    try:
        run(args)
    except Text2qtiError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


def run(args):
    '''
    Convert a quiz file using parsed command-line arguments.
    '''
    config = Config()
    config.load()
    if args.latex_render_url is not None:
        config['latex_render_url'] = args.latex_render_url
    if args.run_code_blocks is not None:
        config['run_code_blocks'] = args.run_code_blocks
    if args.pandoc_mathml is not None:
        config['pandoc_mathml'] = args.pandoc_mathml

    file_path = pathlib.Path(args.file).expanduser()
    file_path_abs = file_path.absolute()
    text = read_quiz_text(file_path)

    if args.solutions:
        qti_path = file_path.parent / f'{file_path.stem}.zip'
        solutions_paths = [pathlib.Path(x).expanduser().absolute() for x in args.solutions]
    elif args.only_solutions:
        qti_path = None
        solutions_paths = [pathlib.Path(x).expanduser().absolute() for x in args.only_solutions]
    else:
        qti_path = file_path.parent / f'{file_path.stem}.zip'
        solutions_paths = None
    if solutions_paths is not None:
        if file_path_abs in solutions_paths:
            raise Text2qtiError(f'Solutions cannot overwrite quiz file "{file_path}"')
        if not all(x.suffix.lower() in ('.md', '.markdown', '.pdf', '.html') for x in solutions_paths):
            invalid_extensions = ', '.join(x.suffix for x in solutions_paths if x.suffix not in ('.md', '.markdown', '.pdf', '.html'))
            raise Text2qtiError(f'Unsupported export format(s) {invalid_extensions} for solutions; use .md, .markdown, .pdf, or .html')
    if args.preview:
        solutions_paths = None
        qti_path = None
    # Quiz and any solutions should only be generated once each so that
    # any randomization is only invoked once.
    quiz = Quiz(text, config=config, source_name=file_path.as_posix(), resource_path=file_path.parent)
    if solutions_paths is not None:
        export_solutions(quiz, solutions_paths)
    if qti_path is not None:
        write_qti(quiz, qti_path)
    if args.preview:
        print(quiz_to_preview_json(quiz), file=sys.stdout)
