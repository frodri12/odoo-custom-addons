# -*- coding: utf-8 -*-

from odoo import models, fields

class L10nPyCity(models.Model):

    _name = "l10n_aipy_city"
    _description = "Paraguay - Cities"

    code = fields.Integer()
    name = fields.Char()

    country_id = fields.Many2one("res.country")
    district_id = fields.Many2one("l10n_aipy_district")
    
