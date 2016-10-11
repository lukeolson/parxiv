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
-rw-r--r--   1 lukeo  staff    14K Jun 30 11:10:16 2016 refs.bib
-rw-r--r--   1 lukeo  staff   190B Oct 10 21:01:38 2016 extra.txt
drwxr-xr-x  28 lukeo  staff   952B Jul 12 14:22:13 2016 figures
-rw-r--r--   1 lukeo  staff   8.8K Jul  1 07:52:56 2016 paper.bbl
-rw-r--r--   1 lukeo  staff   1.1M Jul  1 07:52:58 2016 paper.pdf
-rw-r--r--   1 lukeo  staff    91K Aug 15 10:04:00 2016 paper.tex
-rwxr-xr-x   1 lukeo  staff    49K Feb 11 19:01:50 2016 siamart.cls
-rwxr-xr-x   1 lukeo  staff    20K Feb 11 19:01:50 2016 siamplain.bst
```
and make a new directory `arxiv-Mon-Oct-10-18-55-29-2016` with:

```
-rw-r--r--  1 lukeo  staff    68K Jun 29 11:16:19 2016 myfig.pdf
-rw-r--r--  1 lukeo  staff    68K Jun 29 11:16:28 2016 myotherfig.pdf
-rw-r--r--  1 lukeo  staff    66K Jun 29 13:28:48 2016 aggregate-rootnode.pdf
-rw-r--r--  1 lukeo  staff   332K Oct 10 19:42:44 2016 cleveref.sty
-rw-r--r--  1 lukeo  staff    42K Oct 10 20:39:21 2016 ntheorem.sty
-rw-r--r--  1 lukeo  staff   8.8K Jul  1 07:52:56 2016 paper_strip.bbl
-rw-r--r--  1 lukeo  staff    89K Oct 10 20:49:32 2016 paper_strip.tex
-rwxr-xr-x  1 lukeo  staff    49K Oct 10 20:41:28 2016 siamart.cls*
-rwxr-xr-x  1 lukeo  staff    20K Feb 11 19:01:50 2016 siamplain.bst*
```

The structure is flat.  Then `tar cvfz arxiv-Mon-Oct-10-18-55-29-2016.tgz arxiv-Mon-Oct-10-18-55-29-2016` and you're ready to upload the `.tgz` file.

## what may go wrong

    - multiple graphics paths (TODO)
    - arxiv may need an extra file; put this (local) file into extra.txt
