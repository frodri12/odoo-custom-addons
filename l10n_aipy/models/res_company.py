# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, Command, SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)

class Company(models.Model):

    _inherit = "res.company"

    l10n_aipy_house = fields.Char(
        "House", compute='_compute_address', inverse='_inverse_house')
    l10n_aipy_district_id = fields.Many2one(
        "l10n_aipy_district", compute='_compute_address', inverse='_inverse_district')
    l10n_aipy_city_id = fields.Many2one(
        "l10n_aipy_city", compute='_compute_address', inverse='_inverse_cityId')

    l10n_aipy_dnit_organization = fields.Integer("Organization", default = 1)

    l10n_aipy_enable_edi = fields.Boolean("Enable EDI", default=False)
    l10n_aipy_testing_mode = fields.Boolean("Testing Mode", default=True)

    l10n_aipy_dnit_auth_code = fields.Char("Numero de Timbrado")
    l10n_aipy_dnit_auth_date = fields.Date("Fecha del Timbrado")
    l10n_aipy_dnit_auth_code_test = fields.Char("Numero de Timbrado (Test)")
    l10n_aipy_dnit_auth_date_test = fields.Date("Fecha del Timbrado (Test)")

    l10n_aipy_economic_activity_ids = fields.One2many(
        'l10n_aipy.economic.activity', 'company_id',
        string='Economic Activities',
        help='Economic activities associated with the country'
    )

    l10n_aipy_fantasy_name = fields.Char( string='Fantasy Name')

    l10n_aipy_regime_type_id = fields.Many2one(
        'l10n_aipy.regime.type', string='Regime Type',
        help='Regime type associated with the company'
    )

    def _get_company_address_field_names(self):
        """ Return a list of fields coming from the address partner to match
        on company address fields. Fields are labeled same on both models. """
        return [
            'street', 'l10n_aipy_house', 'street2', 
            'city', 'zip', 'state_id', 'l10n_aipy_district_id', 
            'l10n_aipy_city_id', 'country_id']

    def _inverse_house(self):
        for company in self:
            company.partner_id.l10n_aipy_house = company.l10n_aipy_house

    def _inverse_district(self):
        for company in self:
            company.partner_id.l10n_aipy_district_id = company.l10n_aipy_district_id

    def _inverse_cityId(self):
        for company in self:
            company.partner_id.l10n_aipy_city_id = company.l10n_aipy_city_id
            
