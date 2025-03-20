# -*- coding: utf-8 -*-

from odoo import fields, models

class Uom(models.Model):

    _inherit = 'uom.uom'

    l10n_aipy_dnit_code = fields.Integer(
        'DNIT Code', help='Paraguay: This code will be used on electronic invoice.')
    l10n_aipy_dnit_name = fields.Char(
        'DNIT Name', help='Paraguay: This name will be used on electronic invoice.')
        
