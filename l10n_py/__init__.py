# -*- coding: utf-8 -*-

from . import controllers
from . import models

def _set_change_values(env):
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.country'")
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.currency'")
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.users' AND name = 'user_admin'")
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.partner' AND name = 'partner_admin'")
   