# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import ValidationError

import logging
import re

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_py_house = fields.Char("House")
    l10n_py_district_id = fields.Many2one("l10n_py_district")
    l10n_py_city_id = fields.Many2one("l10n_py_city")

