#!/usr/local/bin/python3
from __future__ import print_function
import glob
import ply.lex
import re
import os
import io
import time
import shutil
import tempfile
import subprocess

# Python2 FileNotFoundError support
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

"""
usage:
    python parxiv.py file.tex

this will make arxiv-somelongdatestring with
    - file_strip.tex (where includegraphics paths are stripped)
    - file_strip.bbl (you should have the .bbl file already)
    - all figures
    - the class file if custom
    - the bib style if custom
    - extra files listed in extra.txt
"""


def strip_comments(source):
    """
    from https://gist.github.com/amerberg/a273ca1e579ab573b499
    """
    tokens = ('PERCENT', 'BEGINCOMMENT', 'ENDCOMMENT', 'BACKSLASH',
              'CHAR', 'BEGINVERBATIM', 'ENDVERBATIM', 'NEWLINE',
              'ESCPCT',
              )
    states = (('linecomment', 'exclusive'),
              ('commentenv', 'exclusive'),
              ('verbatim', 'exclusive')
              )

    if len(tokens) < 1 or len(states) < 1:
        raise ValueError('need tokens and states')

    # Deal with escaped backslashes, so we don't think they're escaping %.
    def t_BACKSLASH(t):
        r"\\\\"
        return t

    # One-line comments
    def t_PERCENT(t):
        r"\%"
        t.lexer.begin("linecomment")

    # Escaped percent signs
    def t_ESCPCT(t):
        r"\\\%"
        return t

    # Comment environment, as defined by verbatim package
    def t_BEGINCOMMENT(t):
        r"\\begin\s*{\s*comment\s*}"
        t.lexer.begin("commentenv")

    # Verbatim environment (different treatment of comments within)
    def t_BEGINVERBATIM(t):
        r"\\begin\s*{\s*verbatim\s*}"
        t.lexer.begin("verbatim")
        return t

    # Any other character in initial state we leave alone
    def t_CHAR(t):
        r"."
        return t

    def t_NEWLINE(t):
        r"\n"
        return t

    # End comment environment
    def t_commentenv_ENDCOMMENT(t):
        r"\\end\s*{\s*comment\s*}"
        # Anything after \end{comment} on a line is ignored!
        t.lexer.begin('linecomment')

    # Ignore comments of comment environment
    def t_commentenv_CHAR(t):
        r"."
        pass

    def t_commentenv_NEWLINE(t):
        r"\n"
        pass

    # End of verbatim environment
    def t_verbatim_ENDVERBATIM(t):
        r"\\end\s*{\s*verbatim\s*}"
        t.lexer.begin('INITIAL')
        return t

    # Leave contents of verbatim environment alone
    def t_verbatim_CHAR(t):
        r"."
        return t

    def t_verbatim_NEWLINE(t):
        r"\n"
        return t

    # End a % comment when we get to a new line
    def t_linecomment_ENDCOMMENT(t):
        r"\n"
        t.lexer.begin("INITIAL")
        # Newline at the end of a line comment is stripped.

    # Ignore anything after a % on a line
    def t_linecomment_CHAR(t):
        r"."
        pass

    # Error handling rule
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def t_linecomment_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def t_verbatim_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def t_commentenv_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    lexer = ply.lex.lex()
    lexer.input(source)
    return u"".join([tok.value for tok in lexer])


def find_class(source):
    """
    (unused)

    look for \documentclass[review]{siamart}
        then return 'siamart.cls'
    """

    classname = re.search(r'\\documentclass.*{(.*)}', source)
    if classname:
        classname = classname.group(1) + '.cls'

    return classname


def find_bibstyle(source):
    """
    look for \ bibliographystyle{siamplain}
        then return 'siamplain.bst'
    """

    bibstylename = re.search(r'\\bibliographystyle{(.*)}', source)
    if bibstylename:
        bibstylename = bibstylename.group(1) + '.bst'

    return bibstylename


def find_figs(source):
    """
    look for \graphicspath{{subdir}}  (a single subdir)

    find figures in \includegraphics[something]{PATH/filename.ext}
                    \includegraphics{PATH/filename.ext}

    make them       \includegraphics[something]{filename.ext}
                    \includegraphics{filename.ext}

    copy figures to arxivdir
    """

    findgraphicspath = re.search(r'\\graphicspath{(.*)}', source)
    if findgraphicspath:
        graphicspaths = findgraphicspath.group(1)
        graphicspaths = re.findall('{(.*?)}', graphicspaths)
    else:
        graphicspaths = []

    # keep a list of (figname, figpath)
    figlist = []

    def repl(m):

        figpath = ''
        figname = os.path.basename(m.group(2))
        figpath = os.path.dirname(m.group(2))
        newincludegraphics = m.group(1) + figname + m.group(3)

        figlist.append((figname, figpath))
        return newincludegraphics

    source = re.sub(r'(\\includegraphics\[.*?\]{)(.*?)(})', repl, source)

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
            inputname = inputname + '.tex'
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

    dest = re.sub(r'(\\include{)(.*?)(})', repl_include, source, True)
    dest = re.sub(r'(\\input{)(.*?)(})', repl, dest)
    return dest


def main(fname):

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

    print('[parxiv] copying figures', end='')
    allpaths = graphicspaths
    allpaths += ['./']
    for figname, figpath in figlist:

        _, ext = os.path.splitext(figname)
        if ext is '':
            figname += '.pdf'

        if(len(figpath) > 0):
            allpaths = [figpath] + allpaths

        for p in allpaths:
            src = os.path.join(p, figname)
            dest = os.path.join(dirname, os.path.basename(figname))
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
        try:
            d = tempfile.mkdtemp()
            try:
                args = ['pdflatex',
                        '-interaction', 'nonstopmode',
                        '-recorder',
                        '-output-directory', d,
                        newtexfile]
                try:
                    from subprocess import DEVNULL  # Python 3.
                except ImportError:
                    DEVNULL = open(os.devnull, 'wb')
                p = subprocess.Popen(args,
                                     cwd=dirname,
                                     stdin=DEVNULL,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
                stdout, stderr = p.communicate()

                args = ['bibtex', newtexfile.replace('.tex', '.aux')]
                p = subprocess.Popen(args,
                                     cwd=d,
                                     stdin=DEVNULL,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
                stdout, stderr = p.communicate()
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

    return source


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('usage: python parxiv.py <filename.tex>')
        sys.exit(-1)

    fname = sys.argv[1]
    source = main(fname)
