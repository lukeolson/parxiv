#! /usr/bin/env python
"""
The purpose of this script is to generate a clean directory
for upload to Arxiv.  The script has several steps:
    1. read the tex file
    2. strip the comments (leaving a %)
    3. flatten the file for input
    4. re-strip the comments
    5. find figures
    6. make an arxiv directory with a timestamp
    7. copy relevant class/style files
    8. copy figures
    9. copy the bbl file (or generating the bbl file)
    10. copy extra files

usage:
    python parxiv.py file.tex
"""
from __future__ import print_function
import glob
import re
import os
import io
import sys
import time
import shutil
import tempfile
import subprocess
import errno
from collections import defaultdict

import ply.lex

__version__ = '0.2.0'

# Python2 FileNotFoundError support
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

def strip_comments(source):
    """
    from https://gist.github.com/dzhuang/dc34cdd7efa43e5ecc1dc981cc906c85
    """
    tokens = (
                'PERCENT', 'BEGINCOMMENT', 'ENDCOMMENT',
                'BACKSLASH', 'CHAR', 'BEGINVERBATIM',
                'ENDVERBATIM', 'NEWLINE', 'ESCPCT',
                'MAKEATLETTER', 'MAKEATOTHER',
             )
    states = (
                ('makeatblock', 'exclusive'),
                ('makeatlinecomment', 'exclusive'),
                ('linecomment', 'exclusive'),
                ('commentenv', 'exclusive'),
                ('verbatim', 'exclusive')
            )

    # Deal with escaped backslashes, so we don't
    # think they're escaping %
    def t_BACKSLASH(t):
        r"\\\\"
        return t

    # Leaving all % in makeatblock
    def t_MAKEATLETTER(t):
        r"\\makeatletter"
        t.lexer.begin("makeatblock")
        return t

    # One-line comments
    def t_PERCENT(t):
        r"\%"
        t.lexer.begin("linecomment")
        return t  # keep the % as a blank comment

    # Escaped percent signs
    def t_ESCPCT(t):
        r"\\\%"
        return t

    # Comment environment, as defined by verbatim package
    def t_BEGINCOMMENT(t):
        r"\\begin\s*{\s*comment\s*}"
        t.lexer.begin("commentenv")

    #Verbatim environment (different treatment of comments within)
    def t_BEGINVERBATIM(t):
        r"\\begin\s*{\s*verbatim\s*}"
        t.lexer.begin("verbatim")
        return t

    #Any other character in initial state we leave alone
    def t_CHAR(t):
        r"."
        return t

    def t_NEWLINE(t):
        r"\n"
        return t

    # End comment environment
    def t_commentenv_ENDCOMMENT(t):
        r"\\end\s*{\s*comment\s*}"
        #Anything after \end{comment} on a line is ignored!
        t.lexer.begin('linecomment')

    # Ignore comments of comment environment
    def t_commentenv_CHAR(t):
        r"."
        pass

    def t_commentenv_NEWLINE(t):
        r"\n"
        pass

    #End of verbatim environment
    def t_verbatim_ENDVERBATIM(t):
        r"\\end\s*{\s*verbatim\s*}"
        t.lexer.begin('INITIAL')
        return t

    #Leave contents of verbatim environment alone
    def t_verbatim_CHAR(t):
        r"."
        return t

    def t_verbatim_NEWLINE(t):
        r"\n"
        return t

    #End a % comment when we get to a new line
    def t_linecomment_ENDCOMMENT(t):
        r"\n"
        t.lexer.begin("INITIAL")

        # Newline at the end of a line comment is presevered.
        return t

    #Ignore anything after a % on a line
    def t_linecomment_CHAR(t):
        r"."
        pass

    def t_makeatblock_MAKEATOTHER(t):
        r"\\makeatother"
        t.lexer.begin('INITIAL')
        return t

    def t_makeatblock_BACKSLASH(t):
        r"\\\\"
        return t

    # Escaped percent signs in makeatblock
    def t_makeatblock_ESCPCT(t):
        r"\\\%"
        return t

    # presever % in makeatblock
    def t_makeatblock_PERCENT(t):
        r"\%"
        t.lexer.begin("makeatlinecomment")
        return t

    def t_makeatlinecomment_NEWLINE(t):
        r"\n"
        t.lexer.begin('makeatblock')
        return t

    # Leave contents of makeatblock alone
    def t_makeatblock_CHAR(t):
        r"."
        return t

    def t_makeatblock_NEWLINE(t):
        r"\n"
        return t

    # For bad characters, we just skip over it
    def t_ANY_error(t):
        t.lexer.skip(1)

    lexer = ply.lex.lex()
    lexer.input(source)
    return u"".join([tok.value for tok in lexer])


def find_class(source):
    r"""
    (unused)

    look for \documentclass[review]{siamart}
        then return 'siamart.cls'
    """

    classname = re.search(r'\\documentclass.*{(.*)}', source)
    if classname:
        classname = classname.group(1) + '.cls'

    return classname


def find_bibstyle(source):
    r"""
    look for \bibliographystyle{siamplain}
        then return 'siamplain.bst'
    """

    bibstylename = re.search(r'\\bibliographystyle{(.*)}', source)
    if bibstylename:
        bibstylename = bibstylename.group(1) + '.bst'

    return bibstylename


from collections import defaultdict

def find_figs(source):
    r"""
    Parse \includegraphics and rename files with duplicate names using their relative path.
    """

    findgraphicspath = re.search(r'\\graphicspath{(.*)}', source)
    if findgraphicspath:
        graphicspaths = re.findall(r'{(.*?)}', findgraphicspath.group(1))
    else:
        graphicspaths = []

    # First pass to count basename occurrences
    matches = re.findall(r'\\includegraphics(?:\[[^\]]*\])?{(.*?)}', source)
    name_counts = defaultdict(int)
    for path in matches:
        name = os.path.basename(path)
        name_counts[name] += 1

    figlist = []
    seen = {}

    def path_to_safe_suffix(path):
        """Convert ./foo/bar/baz.pdf -> baz_foo_bar.pdf"""
        parts = os.path.normpath(path).split(os.sep)
        return "_".join(reversed(parts)).replace('.', '_', parts[-1].count('.'))

    def repl(m):
        prefix, path, suffix = m.group(1), m.group(2), m.group(3)
        base = os.path.basename(path)
        dirpath = os.path.dirname(path).lstrip('./')

        if name_counts[base] > 1:
            key = os.path.normpath(path)
            if key not in seen:
                stem, ext = os.path.splitext(base)
                rel_path = os.path.normpath(path).lstrip('./')
                path_suffix = rel_path.replace('/', '_').replace('\\', '_')
                newname = f"{path_suffix}"
                seen[key] = newname
            else:
                newname = seen[key]
        else:
            newname = base

        figlist.append((base, dirpath, newname))
        return f"{prefix}{newname}{suffix}"

    source = re.sub(r'(\\includegraphics(?:\[[^\]]*\])?{)(.*?)(})', repl, source, flags=re.DOTALL)
    return figlist, source, graphicspaths



def flatten(source):
    """
    replace arguments of include{} and intput{}

    only input can be nested

    include adds a clearpage

    includeonly not supported
    """

    def repl(m):
        inputname = m.group(2)
        if not os.path.isfile(inputname):
            if os.path.isfile(inputname + '.tex'):
                inputname = inputname + '.tex'
            elif os.path.isfile(inputname + '.tikz'):
                inputname = inputname + '.tikz'
            else:
                raise NameError(f'File {inputname}.tex or .tikz not found.')
        with io.open(inputname, encoding='utf-8') as f:
            newtext = f.read()
        newtext = re.sub(r'(\\input{)(.*?)(})', repl, newtext)
        return newtext

    def repl_include(m):
        inputname = m.group(2)
        if not os.path.isfile(inputname):
            inputname = inputname + '.tex'
        with io.open(inputname, encoding='utf-8') as f:
            newtext = f.read()
        newtext = '\\clearpage\n' + newtext
        newtext = re.sub(r'(\\input{)(.*?)(})', repl, newtext)
        newtext += '\\clearpage\n'
        return newtext

    dest = re.sub(r'(\\include{)(.*?)(})', repl_include, source)
    dest = re.sub(r'(\\input{)(.*?)(})', repl, dest)
    return dest


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("fname", metavar="filename.tex", help="name of texfile to arxiv")
    args = parser.parse_args()
    fname = args.fname

    print('[parxiv] reading %s' % fname)
    with io.open(fname, encoding='utf-8') as f:
        source = f.read()

    print('[parxiv] stripping comments')
    source = strip_comments(source)
    print('[parxiv] flattening source')
    source = flatten(source)
    print('[parxiv] stripping comments again')
    source = strip_comments(source)
    print('[parxiv] finding figures...')
    figlist, source, graphicspaths = find_figs(source)
    # print('[parxiv] finding article class and bib style')
    # localbibstyle = find_bibstyle(source)

    print('[parxiv] making directory', end='')
    dirname = 'arxiv-' + time.strftime('%c').replace(' ', '-')
    dirname = dirname.replace(':', '-')
    print(' %s' % dirname)
    os.makedirs(dirname)

    print('[parxiv] copying class/style files')
    # shutil.copy2(localclass, os.path.join(dirname, localclass))
    # if localbibstyle is not None:
    #     shutil.copy2(localbibstyle, os.path.join(dirname, localbibstyle))
    for bst in glob.glob('*.bst'):
        shutil.copy2(bst, os.path.join(dirname, bst))
    for sty in glob.glob('*.sty'):
        shutil.copy2(sty, os.path.join(dirname, sty))
    for cls in glob.glob('*.cls'):
        shutil.copy2(cls, os.path.join(dirname, cls))

    print('[parxiv] copying figures')
    for figname, figpath, newfigname in figlist:
        allpaths = graphicspaths
        allpaths += ['./']

        _, ext = os.path.splitext(figname)
        if ext == '':
            figname += '.pdf'
            newfigname += '.pdf'

        if figpath:
            allpaths = [os.path.join(p, figpath) for p in allpaths]

        for p in allpaths:

            #if 'quartz' in newfigname:
            #    print(p)

            src = os.path.join(p, figname)
            dest = os.path.join(dirname, os.path.basename(newfigname))
            try:
                shutil.copy2(src, dest)
            except IOError:
                # attempts multiple graphics paths
                pass

    # copy bbl file
    print('[parxiv] copying bbl file')
    bblfile = fname.replace('.tex', '.bbl')
    newbblfile = fname.replace('.tex', '_strip.bbl')
    bblflag = False
    try:
        shutil.copy2(bblfile, os.path.join(dirname, newbblfile))
        bblflag = True
    except FileNotFoundError:
        print('          ...skipping, not found')

    # copy extra files
    try:
        with io.open('extra.txt', encoding='utf-8') as f:
            inputsource = f.read()
    except IOError:
        print('[parxiv] copying no extra files')
    else:
        print('[parxiv] copying extra file(s): ', end='')
        for f in inputsource.split('\n'):
            if os.path.isfile(f):
                localname = os.path.basename(f)
                print(' %s' % localname, end='')
                shutil.copy2(f, os.path.join(dirname, localname))
        print('\n')

    newtexfile = fname.replace('.tex', '_strip.tex')
    print('[parxiv] writing %s' % newtexfile)
    with io.open(
            os.path.join(dirname, newtexfile), 'w') as fout:
        fout.write(source)

    print('[parxiv] attempting to generate bbl file')
    if not bblflag:
        # attempt to generate
        # with tempfile.TemporaryDirectory() as d:
        # python2 support
        try:
            d = tempfile.mkdtemp()
            try:
                args = ['pdflatex',
                        '-interaction', 'nonstopmode',
                        '-recorder',
                        '-output-directory', d,
                        newtexfile]
                # python2 support
                try:
                    from subprocess import DEVNULL
                except ImportError:
                    DEVNULL = open(os.devnull, 'wb')
                p = subprocess.Popen(args,
                                     cwd=dirname,
                                     stdin=DEVNULL,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
                p.communicate()

                # copy .bib files
                for bib in glob.glob('*.bib'):
                    shutil.copy2(bib, os.path.join(d, bib))
                for bib in glob.glob('*.bst'):
                    shutil.copy2(bib, os.path.join(d, bib))

                args = ['bibtex', newtexfile.replace('.tex', '.aux')]
                p = subprocess.Popen(args,
                                     cwd=d,
                                     stdin=DEVNULL,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
                p.communicate()
            except OSError as e:
                raise RuntimeError(e)

            bblfile = newtexfile.replace('.tex', '.bbl')
            if os.path.isfile(os.path.join(d, bblfile)):
                print('         ... generated')
                shutil.copy2(os.path.join(d, bblfile),
                             os.path.join(dirname, bblfile))
            else:
                print('         ... could not generate')
        finally:
            try:
                shutil.rmtree(d)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

if __name__ == '__main__':
    main()
