#!/usr/bin/env python
"""Convert a master latex file,
into a single document by including
automatically all the LaTeX documents
which are arguments of
\include or \input
ignoring any \includeonly
https://gist.github.com/rescolo/4207109
"""


def flatten(masterfile, flattenfile=None):
    filetex = open(masterfile, 'r')
    texlist = filetex.readlines()
    finaltex = open(flattenfile, 'w')
    for i in texlist:
        if i.find(r'\input{') == 0 or i.find(r'\include{') == 0:
            includetex = open(i.split('{')[-1].split('}')[0]+'.tex', 'r')
            finaltex.write(includetex.read())
            finaltex.write('\n')
        elif i.find(r'\includeonly{') == 0:
            finaltex.write(i.replace(r'\includeonly{', r'%\includeonly{'))
        else:
            finaltex.write(i)

    filetex.close()
    finaltex.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        sys.exit('USAGE: %s masterfile.tex flattenfile.tex' % sys.argv[0])

    fname = sys.argv[1]
    flatten(sys.argv[1], sys.argv[2])
