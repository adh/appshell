from flask import render_template, jsonify, request
from markupsafe import Markup
from appshell.templates import TemplateProxy

default_colorset = [
    "#4D4D4D",
    "#5DA5DA",
    "#FAA43A",
    "#60BD68",
    "#F17CB0",
    "#B2912F",
    "#B276B2",
    "#DECF3F",
    "#F15854"
]


t = TemplateProxy('appshell/chart_elements.html')


class Chart(object):
    def __init__(self, name=None,
                 colorset=default_colorset,
                 options=None,
                 height=200,
                 legend=True):
        self.name = name
        self.colorset = colorset
        if options:
            self.options = options
        else:
            self.options = {"responsive": True}
            
        self.height = height
        if name:
            self.name = name
        else:
            self.name = "as-chart-{}".format(id(self))

        self.canvas_style = "height: {}px".format(height)

        self.legend = legend
        
    def __html__(self):
        return t.chart(self)

    @property
    def legend_html(self):
        return t.legend(self.data)
    
class PieChart(Chart):
    __chart_class__ = "Pie"

    def __init__(self, **kwargs):
        super(PieChart, self).__init__(**kwargs);
        self._data = []

    def add(self, value, label, color=None):
        if color is None:
            color = self.colorset[len(self._data) % len(self.colorset)]
            
        self._data.append({"value": value,
                           "color": color,
                           "label": label})

    @property
    def data(self):
        dr = []
        s = 0
        for i in self._data:
            s += i["value"]
            dr.append(dict(i))

        if s == 0:
            s = 1
            
        for i in dr:
            i["label"] = "{}% {}".format(int(i["value"] * 100 / s),
                                         i["label"])

        return dr
        
    
class DoughnutChart(PieChart):
    __chart_class__ = "Doughnut"

class LineChart(Chart):
    __chart_class__ = "Line"
    
    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs);
        self._datasets = []
        self._labels = []

    @property
    def data(self):
        return {"datasets": self._datasets,
                "labels": self._labels}

    def set_labels(self, labels):
        self._labels = labels

    def add_dataset(self, data, label, color=None, fill='rgba(0,0,0,0)'):
        if color is None:
            color = self.colorset[len(self._datasets) % len(self.colorset)]
            
        self._datasets.append({"data": data,
                               "color": color,
                               "pointColor": color,
                               "strokeColor": color,
                               "fillColor": fill,
                               "label": label})
    @property
    def legend_html(self):
        return t.legend(self._datasets)

class BarChart(LineChart):
    __chart_class__ = "Bar"
    
