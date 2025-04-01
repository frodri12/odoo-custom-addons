# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountTax(models.Model):

    _inherit = "account.tax"

    l10n_aipy_tax_base = fields.Float(string='Base Imponible', 
          help='Base imponible para el cálculo del impuesto', default = 100.0)

    l10n_aipy_tax_type = fields.Selection([
        ('1', 'IVA'),
        ('2', 'ISC'),
        ('3', 'Renta'),
        ('4', 'Ninguno'),
        ('5', 'IVA - Renta'),
    ], string='Tipo de impuesto', default='1',
       help='Tipo de impuesto para el cálculo del mismo')

          
