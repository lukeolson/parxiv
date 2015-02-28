# clean-latex-to-arxiv

a simple script to assist in making a clean directory to upload to arxiv

usage:
    python parxiv.py file.tex

this will make arxiv-somelongdatestring with
    - file_strip.tex (where includegraphics paths are stripped)
    - file_strip.bbl (you should have teh .bbl file already)
    - all figures
