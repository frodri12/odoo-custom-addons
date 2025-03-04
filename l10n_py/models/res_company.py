# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, Command, SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)

class Company(models.Model):

    _inherit = "res.company"

    l10n_py_house = fields.Char(
        "House", compute='_compute_address', inverse='_inverse_house')
    l10n_py_district_id = fields.Many2one(
        "l10n_py_district", compute='_compute_address', inverse='_inverse_district')
    l10n_py_city_id = fields.Many2one(
        "l10n_py_city", compute='_compute_address', inverse='_inverse_cityId')

    def _get_company_address_field_names(self):
        """ Return a list of fields coming from the address partner to match
        on company address fields. Fields are labeled same on both models. """
        return [
            'street', 'l10n_py_house', 'street2', 
            'city', 'zip', 'state_id', 'l10n_py_district_id', 
            'l10n_py_city_id', 'country_id']

    def _inverse_house(self):
        for company in self:
            company.partner_id.l10n_py_house = company.l10n_py_house

    def _inverse_district(self):
        for company in self:
            company.partner_id.l10n_py_district_id = company.l10n_py_district_id

    def _inverse_cityId(self):
        for company in self:
            company.partner_id.l10n_py_city_id = company.l10n_py_city_id
            