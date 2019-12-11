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
ຘ
ℿ
ᄑ
ᄏ
ᄐ
ᄓ
ᆩ
፧
፨
።
፠
ᐧ
ᐩ
Ⅲ
ᐱ
ᐳ
ᐯ
ᐸ
←
↑
→
↓
↖
↗
↘
↙
⇐
⏎

⏹
⏸
⏺
⏩
⏪
⏫
⏬
⏭
⏮
⏯

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

█ ▓  ▒      ░   ▢   ▦       ▧   ⿴


Creating a Diagram File
-----------------------
Use the ``diagram`` command to create a blank diagrm file.