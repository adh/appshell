from flask.ext.babelex import Domain, Babel
import appshell

babel_domain = Domain(appshell.__path__[0])
_ = babel_domain.gettext
lazy_gettext = babel_domain.lazy_gettext

