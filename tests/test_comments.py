"""Tests tex snippets in this directory."""

import os
import glob
import tempfile
import subprocess
from parxiv import strip_comments

templatestart = \
r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{mathtools}
\begin{document}
"""

templateend = \
r"""
\end{document}
"""

def run_latex(tex):
    try:
        with tempfile.TemporaryDirectory() as d:
            temptexfile = os.path.join(d, 'test.tex')
            with open(temptexfile, 'w') as f:
                f.write(tex)
            args = ['pdflatex',
                    '-interaction', 'nonstopmode',
                    '-output-directory', d,
                    '-recorder',
                    temptexfile]
            p = subprocess.Popen(args,
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()
            assert p.returncode==0
    except OSError as e:
        raise RuntimeError(e)

def test_texsnippets():
    texsnippets = glob.glob('tests/test_*.tex')
    print(texsnippets)

    for snippet in texsnippets:
        with open(snippet, 'r') as f:
            textest = f.read()
        tex = templatestart + textest + templateend
        texparsed = strip_comments(tex)
        run_latex(tex)
        run_latex(texparsed)
        print(texparsed)
