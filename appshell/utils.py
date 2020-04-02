from flask import request, g
from appshell.locals import current_appshell
from collections import defaultdict
from werkzeug.local import LocalProxy

def get_pushed_blocks_dict():
    pb = getattr(g, '_appshell_pushed_blocks', None)
    if pb is None:
        pb = g._appshell_pushed_blocks = defaultdict(list)
    return pb

pushed_blocks = LocalProxy(get_pushed_blocks_dict)

def push_block(cls, caller):
    pushed_blocks[cls].append(caller)
    return '' # XXX

def get_pushed_blocks(cls):
    return pushed_blocks[cls]
