# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ResCompany(models.Model):

    _inherit = "res.company"

    l10n_py_dnit_responsibility_type_id = fields.Many2one(
        domain="[('code', 'in', [1, 4, 6])]", related='partner_id.l10n_py_dnit_responsibility_type_id', readonly=False)

    l10n_py_company_requires_vat = fields.Boolean(compute='_compute_l10n_py_company_requires_vat', string='Company Requires Vat?')
    l10n_py_dnit_start_date = fields.Date('Activities Start')

    @api.depends('l10n_py_dnit_responsibility_type_id')
    def _compute_l10n_py_company_requires_vat(self):
        recs_requires_vat = self.filtered(lambda x: x.l10n_py_dnit_responsibility_type_id.code == '1')
        recs_requires_vat.l10n_py_company_requires_vat = True
        remaining = self - recs_requires_vat
        remaining.l10n_py_company_requires_vat = False

    @api.onchange('country_id')
    def onchange_country(self):
        """ Paraguayan companies use round_globally as tax_calculation_rounding_method """
        for rec in self.filtered(lambda x: x.country_id.code == "PY"):
            rec.tax_calculation_rounding_method = 'round_globally'

    def _localization_use_documents(self):
        """ Paraguayan localization use documents """
        self.ensure_one()
        return self.account_fiscal_country_id.code == "PY" or super()._localization_use_documents()

    def write(self, vals):
        if 'l10n_py_dnit_responsibility_type_id' in vals:
            for company in self:
                if vals['l10n_py_dnit_responsibility_type_id'] != company.l10n_py_dnit_responsibility_type_id.id and company.sudo()._existing_accounting():
                    raise UserError(_('Could not change the DNIT Responsibility of this company because there are already accounting entries.'))

        return super().write(vals)


    ########################

    l10n_py_house = fields.Char(
        "House", compute='_compute_address', inverse='_inverse_compute_house')
    l10n_py_district_id = fields.Many2one(
        "l10n_py_district", compute='_compute_address', inverse='_inverse_compute_district')
    l10n_py_city_id = fields.Many2one(
        "l10n_py_city", compute='_compute_address', inverse='_inverse_compute_city')

    def _inverse_compute_house(self):
        for company in self:
            company.partner_id.l10n_py_house = company.l10n_py_house

    def _inverse_compute_district(self):
        for company in self:
            company.partner_id.l10n_py_district_id = company.l10n_py_district_id

    def _inverse_compute_city(self):
        for company in self:
            company.partner_id.l10n_py_city_id = company.l10n_py_city_id

    def _get_company_address_field_names(self):
        """ Return a list of fields coming from the address partner to match
        on company address fields. Fields are labeled same on both models. """
        return [
            'street', 'l10n_py_house', 'street2', 
            'city', 'zip', 'state_id', 'l10n_py_district_id', 
            'l10n_py_city_id', 'country_id']
