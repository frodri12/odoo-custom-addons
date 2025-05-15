# -*- coding: utf-8 -*-

from odoo import models, fields

class L10npyEconomicActivity(models.Model):
    _name = 'l10n_py.economic.activity'
    _description = 'Economic Activity'
    _rec_name = 'name'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    code = fields.Char(
        string='Code',
        required=True,
        help='Code of the economic activity',
    )
    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the economic activity',
    )
    #description = fields.Text(string='Description',help='Description of the economic activity',)
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Indicates if the economic activity is active',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help='Company associated with the economic activity',
    )

    def _get_l10n_py_dnit_ws_economic_avtivity( self):
        eco = {}
        eco.update({"codigo": self.code}) #D131
        eco.update({"descripcion": self.name}) #D132
        return eco