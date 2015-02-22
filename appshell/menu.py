from collections import OrderedDict
from flask import request
from appshell.urls import url_for

class MenuItem(object):
    def __init__(self, text, target=None, url=None,
                 active=False, disabled=False, items=None, values={}):
        if target:
            active = request.endpoint == target
            url = url_for(target, **values)

        self.text = text
        self.active = active

        self.disabled = disabled
        self.url = url
        self.items = items

        self.liattrs = {}
        if active:
            self.liattrs['class'] = self.liattrs.get('class', '') + ' active'

        self.aattrs= {}
        if disabled:
            self.aattrs['class'] = self.aattrs.get('class', '') + ' disabled'
        if url:
            self.aattrs['href'] = url
        if items:
            self.aattrs['class'] = self.aattrs.get('class', '') + ' dropdown-toggle'
            self.liattrs['class'] = self.liattrs.get('class', '') + ' dropdown'
            self.aattrs['role'] = 'button'
            self.aattrs['data-toggle'] = 'dropdown'
    def as_menu_item(self):
        return self

class MenuEntry(object):
    def __init__(self, text, target=None, url=None, values={}, items=[]):
        self.text = text
        self.target = target
        self.url = url
        self.values = values
        self.items = items

    def is_visible(self):
        return True

    def as_menu_item(self):
        if self.is_visible():
            return MenuItem(text=self.text,
                            target=self.target,
                            url=self.url,
                            values=self.values,
                            items=self.items)
        else:
            return None

class MenuGroup(object):
    def __init__(self, items, text=None, active=False):
        self.items = items
        self.text = text
        self.active = active
    def __iter__(self):
        return iter(self.items)
    def __len__(self):
        return len(self.items)

class MenuContainer(OrderedDict):
    def __init__(self, text=None, factory=MenuItem):
        OrderedDict.__init__(self)
        self.text = text
        self.factory = factory

    def get_or_create(self, key, text=None, factory=MenuItem):
        if key not in self:
            c = MenuContainer(text, factory)
            self[key] = c
            return c
        c = self[key]
        if not c.text:
            c.text = text
        return c

    def get_menu_items(self):
        items = []
        for i in self.values():
            item = i.as_menu_item()
            if item:
                items.append(item)
        return items

    def as_menu_item(self):
        items = self.get_menu_items()
        if len(items) == 0:
            return None
            
        active = any((i.active for i in items))
        return self.factory(text=self.text, items=items, active=active)


class MainMenu(object):
    def __init__(self):
        self.items = MenuContainer()

    def ensure_menu(self, name, text=None):
        return self.items.get_or_create(name, text)

    def ensure_group(self, menu, group, text=None):
        return self.ensure_menu(menu).get_or_create(group, text, 
                                                    factory=MenuGroup)

    def add_top_entry(self, item, entry):
        self.items[item] = entry

    def add_entry(self, menu, item, entry, group=''):
        g = self.ensure_group(menu, group)
        g[item] = entry

    def build_real_menu(self):
        return self.items.get_menu_items()


