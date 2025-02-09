"""Define the menu contents, hotkeys, and event bindings.

There is additional configuration information in the EditorWindow class (and
subclasses): the menus are created there based on the menu_specs (class)
variable, and menus not created are silently skipped in the code here.  This
makes it possible, for example, to define a Debug menu which is only present in
the PythonShell window, and a Format menu which is only present in the Editor
windows.

"""
#from importlib.util import find_spec

from .configHandler import MrPythonConf

#   Warning: menudefs is altered in macosxSupport.overrideRootMenu()
#   after it is determined that an OS X Aqua Tk is in use,
#   which cannot be done until after Tk() is first called.
#   Do not alter the 'file', 'options', or 'help' cascades here
#   without altering overrideRootMenu() as well.
#       TODO: Make this more robust

menudefs = [
 # underscore prefixes character to underscore
 ('file', [
   ('_New File', '<<open-new-window>>'),
   ('_Open...', '<<open-window-from-file>>'),
   ('Open _Module...', '<<open-module>>'),
   None,
   ('_Save', '<<save-window>>'),
   ('Save _As...', '<<save-window-as-file>>'),
   ('Save Cop_y As...', '<<save-copy-of-window-as-file>>'),
   None,
   ('_Close', '<<close-window>>'),
   ('E_xit', '<<close-all-windows>>'),
  ]),
 ('edit', [
   ('_Undo', '<<undo>>'),
   ('_Redo', '<<redo>>'),
   None,
   ('Cu_t', '<<cut>>'),
   ('_Copy', '<<copy>>'),
   ('_Paste', '<<paste>>'),
   ('Select _All', '<<select-all>>'),
   None,
   ('_Find...', '<<find>>'),
   ('Find A_gain', '<<find-again>>'),
   ('Find _Selection', '<<find-selection>>'),
   ('Find in Files...', '<<find-in-files>>'),
   ('R_eplace...', '<<replace>>'),
   ('Go to _Line', '<<goto-line>>'),
  ]),
('format', [
   ('_Indent Region', '<<indent-region>>'),
   ('_Dedent Region', '<<dedent-region>>'),
    None,
   ('Comment _Out Region', '<<comment-region>>'),
   ('U_ncomment Region', '<<uncomment-region>>')
   ]),
 ('command', [
     ('Select language...', '<<select-language>>'),
     None,
     ('Check Module', '<<check-module>>'),
     ('Run Module', '<<run-module>>'),
 ]),
    ('help', [
   ('_About MrPython', '<<about-mrpython>>'),
   None,
   ('_MrPython Help', '<<help>>'),
   ('Python _Docs', '<<python-docs>>'),
   ]),
]

#if find_spec('turtledemo'):
 #   menudefs[-1][1].append(('Turtle Demo', '<<open-turtle-demo>>'))

default_keydefs = MrPythonConf.GetCurrentKeySet()

