# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ResCompany(models.Model):

    _inherit = "res.company"

    l10n_py_regime_type_id = fields.Many2one(
        'l10n_py.regime.type', string='Regime Type',
        help='Regime type associated with the company'
    )

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
                    raise UserError(_('Could not change the Responsibility of this company because there are already accounting entries.'))

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

        
    ########################

    l10n_py_establecimiento = fields.Integer( string="Establishment", default=1)
    
    ########################
    l10n_aipy_economic_activity_ids = fields.One2many(
        'l10n_py.economic.activity', 'company_id',
        string='Economic Activities',
        help='Economic activities associated with the country'
    )

    def _get_l10n_py_dnit_ws_establecimiento( self):
        est = {}
        est.update({"codigo": "%03d" % self.l10n_py_establecimiento})
        est.update({"direccion": self.street}) #D107
        est.update({"numeroCasa": self.l10n_py_house if self.l10n_py_house else 0}) #D108
        if self.street2:
            est.update({"complementoDireccion1": self.street2}) #D109
        est.update({"departamento": int(self.state_id.code)}) #D111
        est.update({"distrito": int(self.l10n_py_district_id.code)}) #D113
        est.update({"ciudad": int(self.l10n_py_city_id.code)}) #D115
        if self.phone:
            if self.phone.__len__() < 6 or self.phone.__len__() > 15:
                raise UserError(_("Phone number must be between 6 and 15 digits"))
            else:
                est.update({"telefono": self.phone}) #D117
        else:
            raise UserError(_("Phone number is required"))
        if self.email:
            if self.email.find(",") > -1:
                est.update({"email": self.email.split(",")[0]}) #D118
            else:
                est.update({"email": self.email}) #D118
        else:
            raise UserError(_("Email is required"))
        estabecimientos = []
        estabecimientos.append(est)
        return estabecimientos

    def _get_l10n_py_dnit_ws_economic_activities( self):
        ecos = []
        ecos_count = 0
        for rec in self.l10n_aipy_economic_activity_ids:
            ecos.append(rec._get_l10n_py_dnit_ws_economic_avtivity())
            ecos_count += 1
        if ecos_count == 0:
            raise UserError(_("Economic activity is required for te company"))
        return ecos
