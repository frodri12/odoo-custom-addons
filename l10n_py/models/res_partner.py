# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import ValidationError

import logging
import re

_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = (
    'street', 'l10n_py_house', 'street2', 
    'zip', 'city', 'state_id', 'l10n_py_district_id', 
    'l10n_py_city_id', 'country_id')

class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_py_house = fields.Char("House")
    l10n_py_district_id = fields.Many2one("l10n_py_district")
    l10n_py_city_id = fields.Many2one("l10n_py_city")

    @api.model
    def default_get(self,fields_list):
        res = super().default_get(fields_list)
        res.update(
            {'country_id':self.env['res.country'].search([('code', '=', 'PY')], limit=1).id}
        )
        res.update({'lang':self.env.lang})
        return res

    @api.onchange('country_id','l10n_py_city_id')
    def _onChange_City(self):
        if self.country_id.code == 'PY' and self.l10n_py_city_id.country_id.code == 'PY' :
            self.write({'city': self.l10n_py_city_id.name,})
