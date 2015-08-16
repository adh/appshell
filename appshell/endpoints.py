from appshell.base import View
from appshell.templates import confirmation, message
from flask import request, flash, redirect
from flask.ext.babelex import Babel, Domain

mydomain = Domain('appshell')
_ = mydomain.gettext
lazy_gettext = mydomain.lazy_gettext


class ConfirmationEndpoint(View):
    methods = ("GET", "POST")
    redirect_to = None
    
    def prepare(self):
        pass
    
    def dispatch_request(self, **args):
        self.prepare(**args)
        if request.method == "POST":
            self.do_it(**args)
            
            return self.done()
        else:
            return confirmation(self.confirmation_message)
        
    def done(self):
        if self.flash_message:
            flash(*self.flash_message)
        if self.redirect_to:
            return redirect(self.redirect_to)
        return message(_("Done"))
