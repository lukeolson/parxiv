#!/usr/local/bin/python
"""
usage:
    python parxiv.py file.tex

this will make arxiv-somelongdatestring with
    - file_strip.tex (where includegraphics paths are stripped)
    - file_strip.bbl (you should have teh .bbl file already)
    - all figures
"""


def strip_comments(source):
    """
    from https://gist.github.com/amerberg/a273ca1e579ab573b499
    """
    import ply.lex
    tokens = ('PERCENT', 'BEGINCOMMENT', 'ENDCOMMENT', 'BACKSLASH',
              'CHAR', 'BEGINVERBATIM', 'ENDVERBATIM', 'NEWLINE',
              'ESCPCT',
              )
    states = (('linecomment', 'exclusive'),
              ('commentenv', 'exclusive'),
              ('verbatim', 'exclusive')
              )

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
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    lexer = ply.lex.lex()
    lexer.input(source)
    return u"".join([tok.value for tok in lexer])


def find_figs(source):
    """
    find figures in \includegraphics[something]{PATH/filename.ext}
                    \includegraphics{PATH/filename.ext}

    make them       \includegraphics[something]{filename.ext}
                    \includegraphics{filename.ext}
    """
    import re
    import os

    r = re.compile(r'(\includegraphics\[.*?\]{)(.*?)(})')

    # list of figs with the relative path
    figstmp = r.findall(source)
    figs = [fig[1] for fig in figstmp]

    # replace the relative path with .
    source = r.sub(lambda x:
                   x.group(1) +
                   os.path.basename(x.group(2)) +
                   x.group(3), source)
    figstmp = r.findall(source)
    nfigs = [fig[1] for fig in figstmp]

    return figs, source


def main(fname):
    import io
    import time
    import os
    import shutil
    import glob

    with io.open(fname, encoding='utf-8') as f:
        source = f.read()

    source = strip_comments(source)
    figs, source = find_figs(source)

    dirname = 'arxiv-' + time.strftime('%c').replace(' ', '-')
    dirname = dirname.replace(':', '-')
    os.makedirs(dirname)
    for fig in figs:
        try:
            shutil.copy2(fig, os.path.join(dirname, os.path.basename(fig)))
        except:
            base = os.path.join(dirname, os.path.basename(fig))
            for newfig in glob.glob(base+'.*'):
                shutil.copy2(fig, os.path.join(dirname, os.path.basename(fig)))

    bblfile = fname.replace('.tex', '.bbl')
    newbblfile = fname.replace('.tex', '_strip.bbl')
    shutil.copy2(bblfile, os.path.join(dirname, newbblfile))

    with io.open(
            os.path.join(dirname, fname.replace('.tex', '_strip.tex')),
            'w') as fout:
        fout.write(source)

    return source

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('usage: python parxiv.py <filename.tex>')
        sys.exit(-1)

    fname = sys.argv[1]
    source = main(fname)
