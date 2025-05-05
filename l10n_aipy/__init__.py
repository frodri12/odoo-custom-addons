# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID

from . import controllers
from . import models
from . import demo

def install_languages(cr, registry):
    """ Post init function """
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Install desired language (e.g., German)
    lang_es = env['base.language.install'].create({'lang_ids': '80', 'overwrite': False})
    env['base.language.install'].lang_install()

def _set_change_values(env):
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.country'")
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.currency'")
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.users' AND name = 'user_admin'")
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.partner' AND name = 'partner_admin'")
   install_languages(env.cr, env.registry)
   