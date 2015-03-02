from flask import request

def visibility_proc_for_view(view):
    if hasattr(view, '_appshell__visibility_proc'):
        return view._appshell__visibility_proc
    else:
        return None

def attach_view_visibility(view, proc):
    old = visibility_proc_for_view(view)
    if old:
        def visibilty_proc(**kwargs):
            if not proc(**kwargs):
                return False
            else:
                return old(**kwargs)
            view._appshell__visibility_proc = visibility_proc
    else:
        view._appshell__visibility_proc = proc


def view_visible(view):
    def wrap(func):
        attach_view_visibility(view, func)
        return func
    return wrap
