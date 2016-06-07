from flask.ext.babelex import Babel, Domain
import xlsxwriter
import csv
from flask import jsonify
from io import StringIO, BytesIO
import json

mydomain = Domain('appshell')
_ = mydomain.gettext
lazy_gettext = mydomain.lazy_gettext

def xlsx_exporter(data, ds):
    f = BytesIO()

    wb = xlsxwriter.Workbook(f, {"default_date_format": "yyyy-mm-dd hh:mm:ss"})
    ws = wb.add_worksheet()

    widths = [0 for i in ds.columns]
    
    for col, j in enumerate(ds.columns):
        ws.write(0, col, j.name)
        w = len(str(j.name))
        if w > widths[col]:
            widths[col] = w

    row = 1
    for i in data["raw_data"]:
        for col, j in enumerate(i):
            try:
                ws.write(row, col, j)
            except TypeError:
                ws.write(row, col, str(j))
            w = len(str(j))
            if w > widths[col]:
                widths[col] = w
        row += 1

    for x, i in enumerate(widths):
        ws.set_column('{0}:{0}'.format(chr(x + ord('A'))), i + 2)

    wb.close()

    return (f.getvalue(), 200, 
            {"Content-Type": 
             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             "Content-Disposition": 
             "attachment; filename={0}.xlsx".format(ds.name)})

def csv_exporter(data, ds):
    f = StringIO()
    w = csv.writer(f)

    w.writerow([i.name for i in ds.columns])
    
    for i in data["raw_data"]:
        w.writerow([j for j in i])
        
    return (f.getvalue().encode("utf-8"), 200, 
            {"Content-Type": "text/csv",
             "Content-Disposition": 
             "attachment; filename={0}.csv".format(ds.name)})

def json_exporter(data, ds):
    return (json.dumps(data["raw_data"]), 200, 
            {"Content-Type": "application/json",
             "Content-Disposition": 
             "attachment; filename={0}.json".format(ds.name)})
    

def xlsx_register(ds):
    ds.register_action("export-xlsx", lazy_gettext('XLSX Export'),
                       xlsx_exporter)
def csv_register(ds):
    ds.register_action("export-csv", lazy_gettext('CSV Export'),
                       csv_exporter)
def json_register(ds):
    ds.register_action("export-json", lazy_gettext('JSON Export'),
                       json_exporter)

def all(ds):
    csv_register(ds)
    xlsx_register(ds)
    json_register(ds)
