from flask.ext.babelex import Domain, Babel
import flask
from .. import translations

babel_domain = Domain(translations.__path__[0])
_ = babel_domain.gettext
gettext = babel_domain.gettext
pgettext = babel_domain.pgettext
ngettext = babel_domain.ngettext
npgettext = babel_domain.npgettext
lazy_gettext = babel_domain.lazy_gettext
lazy_pgettext = babel_domain.lazy_pgettext
