from flask_assets import Environment, Bundle

assets = Environment()

appshell_components_css = Bundle(
    'appshell/datatables/css/dataTables.bootstrap.css',
    'appshell/datatables/css/dataTables.fixedHeader.css',
    'appshell/datatables/css/dataTables.fixedColumns.min.css',
    'appshell/datatables/css/dataTables.scroller.min.css',
    'appshell/datatables/css/dataTables.colReorder.min.css',
    'appshell/fontawesome/css/font-awesome.css',
    'appshell/treegrid/css/jquery.treegrid.css',
    'appshell/datepicker/css/datepicker3.css',
    'appshell/bootstrap-markdown/css/bootstrap-markdown.min.css',
    'appshell/bs-select/css/bootstrap-select.min.css',
    filters='cssutils', output="gen/appshell/styles.css")
assets.register("appshell_components_css", appshell_components_css)

appshell_css = Bundle('appshell/appshell.css',
                      appshell_components_css,
                      filters='cssutils', output="gen/appshell/styles.css")
assets.register("appshell_css", appshell_css)

appshell_js = Bundle('appshell/datatables/js/jquery.dataTables.min.js',
                     'appshell/datatables/js/dataTables.bootstrap.js',
                     'appshell/datatables/js/dataTables.fixedHeader.js',
                     'appshell/datatables/js/dataTables.fixedColumns.min.js',
                     'appshell/datatables/js/dataTables.colReorder.min.js',
                     'appshell/datatables/js/dataTables.scroller.min.js',
                     'appshell/treegrid/js/jquery.cookie.js',
                     'appshell/treegrid/js/jquery.treegrid.js',
                     'appshell/treegrid/js/jquery.treegrid.bootstrap3.js',
                     'appshell/datepicker/js/bootstrap-datepicker.js',
                     'appshell/bootstrap-markdown/js/bootstrap-markdown.js',
                     'appshell/bootstrap-markdown/js/markdown.js',
                     'appshell/bootstrap-markdown/js/to-markdown.js',
                     'appshell/bs-select/js/bootstrap-select.min.js',
                     'appshell/Chart.min.js',
                     'appshell/appshell.js',
                     filters=None, output="gen/appshell/scripts.js"
)
assets.register("appshell_js", appshell_js)

