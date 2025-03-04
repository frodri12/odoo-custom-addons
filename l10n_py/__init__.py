# -*- coding: utf-8 -*-

from . import controllers
from . import models

def _set_change_values(env):
   env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model = 'res.country'")
