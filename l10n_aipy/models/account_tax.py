# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountTax(models.Model):

    _inherit = "account.tax"

    l10n_aipy_tax_base = fields.Float(string='Base Imponible', 
          help='Base imponible para el cálculo del impuesto', default = 100.0)

          
