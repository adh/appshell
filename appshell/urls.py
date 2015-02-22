from flask import request
import flask

res_url = flask.url_for

def url_for(path, **kwargs):
    for k, v in request.args.iteritems():
        if k.startswith('__'):
            kwargs[k] = v
    return flask.url_for(path, **kwargs)

def url_filter(fun):
    def url_or_url_for(path, **kwargs):
        if '/' in path:
            return path.format(**kwargs)
        else:
            return fun(path, **kwargs)
    return url_or_url_for

url_or_res_url = url_filter(res_url)
url_or_url_for = url_filter(url_for)
