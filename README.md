# clean-latex-to-arxiv

a simple script to assist in making a clean directory to upload to arxiv

usage:
    python parxiv.py file.tex

this will make arxiv-somelongdatestring with

    - file_strip.tex (where includegraphics paths are stripped)
    - file_strip.bbl (you should have the .bbl file already)
    - all figures
    - all figures
    - the class file if custom
    - the bib style if custom
    - extra files listed in extra.txt

## what may go wrong

    - multiple graphics paths (TODO)
    - arxiv may need an extra file; put this (local) file into extra.txt
