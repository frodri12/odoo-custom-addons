# -*- coding: utf-8 -*-

from odoo import fields, models

class ResCountry(models.Model):

    _inherit = 'res.country'

    l10n_py_alpha_code = fields.Char(
        'Alpha3 Code', size=3, help='This code will be used on electronic invoice')
    l10n_py_alpha_number = fields.Char(
        'ISO Number'
    )