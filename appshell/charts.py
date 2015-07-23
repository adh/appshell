from flask import render_template, jsonify, request
from markupsafe import Markup

default_colorset = [
    ("#3c763d", "#dff0d8"),
    ("#31708f", "#d9edf7"),
    ("#8a6d3b", "#fcf8e3"),
    ("#a94442", "#f2dede")
]

class Chart(object):
    def __init__(self, name, colorset=None):
        self.name = name
        self.colorset = colorset

class PieChart(Chart):
    def __init__(self, name, ):
        pass
