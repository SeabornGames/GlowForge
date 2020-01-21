Glowforge Model Home
====================

This project is to take a diagram of a house and draw the shapes needed to
cut it out and build a model of the house.

Install library
===============

Ensure you have python 3.6 or better.

To create a private virtual environment use the following command:
>> python3.6 -m venv --clear ./venv
>> ./venv/bin/pip install .


Defining the Diagram
====================

The first step is to define the diagram of the house and for this we will use
the following shapes.  Real boundary walls will be made with = and imaginary,
windows, and doors will be made with -.  It is assuming each character is 4" by
4".

https://www.fileformat.info/info/charset/UTF-8/list.htm?start=8192
https://cloford.com/resources/charcodes/utf-8_box-drawing.htm
ຘℿᄑᄏᄐᄓᆩ፧፨።፠ᐧᐩⅢᐱᐳᐯᐸ←↑→↓↖↗↘↙⇐⏎
⏹⏸⏺⏩⏪⏫⏬⏭⏮⏯
█ ▓  ▒      ░   ▢   ▦       ▧   ⿴ ▬
﹋﹏

Tops:
    ╔   ╒    ═   ╤   ╕ ╗

Internal
     ─   ┼  ╬  ╪  ╢ │   ║ ╣

Left
    ╠   ╞   ├   │   ╣ ╟

Right
    ╡   ┤   │

Bottom
    ╚ ╘ ╙  ═   ╧  ╩  ╛  ╝  ╜

┃ ━ ┏ ┓ ┗ ┛ ┣ ┫ ┳ ┻ ╋ ┇ ┉

꒿꒾ⅼ

Creating a Diagram File
-----------------------

Use the ``diagram`` command to create a blank diagram file, or to clean up
an existing diagram.


Creating Glowforge Walls
------------------------

The following two files are needed to create the walls for glowforge:
    1. diagram file from above
    2. wall file.

The wall file is a csv table (or any file format that seaborn_table can read.
If the wall file is not provided then the glowforge program will create it based
on the room names in the diagram file.





