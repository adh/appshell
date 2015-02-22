from markupsafe import Markup

def xmlattrs(attrs):
    res = Markup(" ").join(
        Markup('{0}="{1}"').format(k, v) 
        for k, v in attrs.iteritems()
        if v != None
    )
    if res != '':
        return " " + res
    else:
        return ""

def xmltag(name, attrs):
    return Markup("<{0}{1}>").format(name, xmlattrs(attrs))

def element(name, attrs, contents):
    return Markup("{0}{1}</{2}>").format(xmltag(name, attrs),
                                         contents,
                                         name)

def class_button(klass, text, context_class="default", size=None):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    return element("button", 
                   {"class": cls + " " + klass, 
                    "type": "button"},
                   contents)

def link_button(url, text, context_class="default", size=None):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    return element("a", 
                   {"class": cls, "role": "button", "href": url},
                   contents)
