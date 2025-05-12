# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountTax(models.Model):

    _inherit = "account.tax"

    l10n_py_tax_base = fields.Float(string='Tax Base', 
          help='Taxable base for calculating the tax', default = 100.0)
