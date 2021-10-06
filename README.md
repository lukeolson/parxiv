# clean-latex-to-arxiv

a simple script to assist in making a clean directory to upload to arxiv

### Installation

```
pip install -U git+https://github.com/lukeolson/clean-latex-to-arxiv
```

### Usage

    parxiv file.tex

this will make `arxiv-somelongdatestring` with

- file_strip.tex (where includegraphics paths and comments are stripped)
- file_strip.bbl (you should have the .bbl file already -- if not, it will attempt to generate)
- all figures
- local `.bst`, `.cls`, and `.sty` files
- extra files listed in extra.txt

For example, this will take

```
-rw-r--r--  1 501  20    60K Jun  3 08:01:49 2021 amsart.cls
-rw-r--r--  1 501  20     9B Jun  3 08:51:21 2021 extra.txt
drwxr-xr-x  3 501  20    96B Jun  3 08:21:08 2021 figs1/
drwxr-xr-x  3 501  20    96B Jun  3 08:22:07 2021 figs2/
drwxr-xr-x  3 501  20    96B Jun  3 08:37:08 2021 figs3/
-rw-r--r--  1 501  20    11B Jun  3 08:50:40 2021 notes.md
-rw-r--r--  1 501  20   677B Jun  3 09:53:40 2021 paper.tex
-rw-r--r--  1 501  20   236B Jun  3 09:54:25 2021 refs.bib
-rw-r--r--  1 501  20    88B Jun  3 09:08:16 2021 section.tex
-rw-r--r--  1 501  20   100B Jun  3 09:05:50 2021 subsection.tex
-rw-r--r--  1 501  20    86B Jun  3 09:01:32 2021 subsubsection.tex
```
and make a new directory `arxiv-Sun-Jun--3-15-38-51-2021` with:

```
-rw-r--r--  1 501  20    60K Jun  3 08:01:49 2021 amsart.cls
-rw-r--r--  1 501  20   4.1K Jun  3 08:21:08 2021 fig1.pdf
-rw-r--r--  1 501  20   4.3K Jun  3 08:22:07 2021 fig2.pdf
-rw-r--r--  1 501  20   4.4K Jun  3 08:37:08 2021 fig3.pdf
-rw-r--r--  1 501  20    11B Jun  3 08:50:40 2021 notes.md
-rw-r--r--  1 501  20    49B Jun  3 15:38:52 2021 paper_strip.bbl
-rw-r--r--  1 501  20   705B Jun  3 15:38:51 2021 paper_strip.tex
```

The structure is flat.  Then

```
tar cvfz arxiv-Sun-Jun--3-15-38-51-2021.tgz arxiv-Sun-Jun--3-15-38-51-2021`
```

and you're ready to upload the `.tgz` file.

### what may go wrong

    - The `.bbl` file may not be generated.  Pre-generate this.
    - Arxiv may need an extra file; put this (local) file into extra.txt
