# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountTax(models.Model):

    _inherit = "account.tax"

    l10n_py_tax_base = fields.Float(string='Tax Base', 
          help='Taxable base for calculating the tax', default = 100.0)

    l10n_py_tax_type = fields.Selection([
        ('1', 'IVA'),
        ('2', 'ISC'),
        ('3', 'Renta'),
        ('4', 'Ninguno'),
        ('5', 'IVA - Renta'),
        ('P', 'Percepcion'),
        ('R', 'Retencion')
    ], string='Tipo de impuesto', default='1',
       help='Tipo de impuesto para el cálculo del mismo')
