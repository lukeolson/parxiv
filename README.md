# clean-latex-to-arxiv

a simple script to assist in making a clean directory to upload to arxiv

*usage*:

    python parxiv.py file.tex

this will make arxiv-somelongdatestring with

    - file_strip.tex (where includegraphics paths are stripped)
    - file_strip.bbl (you should have the .bbl file already)
    - all figures
    - all figures
    - the class file if custom
    - the bib style if custom
    - extra files listed in extra.txt

This will take

```
-rw-r--r--  refs.bib
-rw-r--r--  extra.txt
drwxr-xr-x  figures
-rw-r--r--  paper.bbl
-rw-r--r--  paper.pdf
-rw-r--r--  paper.tex
-rwxr-xr-x  siamart.cls
-rwxr-xr-x  siamplain.bst
```
and make a new directory `arxiv-Mon-Oct-10-18-55-29-2016` with:

```
-rw-r--r--  myfig.pdf
-rw-r--r--  myotherfig.pdf
-rw-r--r--  aggregate-rootnode.pdf
-rw-r--r--  cleveref.sty
-rw-r--r--  ntheorem.sty
-rw-r--r--  paper_strip.bbl
-rw-r--r--  paper_strip.tex
-rwxr-xr-x  siamart.cls
-rwxr-xr-x  siamplain.bst
```

The structure is flat.  Then `tar cvfz arxiv-Mon-Oct-10-18-55-29-2016.tgz arxiv-Mon-Oct-10-18-55-29-2016` and you're ready to upload the `.tgz` file.

## what may go wrong

    - multiple graphics paths (TODO)
    - arxiv may need an extra file; put this (local) file into extra.txt
