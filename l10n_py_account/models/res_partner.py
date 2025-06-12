# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import stdnum.py.ruc
import re
import logging

_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = (
    'street', 'l10n_py_house', 'street2', 
    'zip', 'city', 'state_id', 'l10n_py_district_id', 
    'l10n_py_city_id', 'country_id')

class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_py_dnit_responsibility_type_id = fields.Many2one(
        'l10n_py.dnit.responsibility.type', string='DNIT Responsibility Type', index='btree_not_null', help='Defined by DNIT to'
        ' identify the type of responsibilities that a person or a legal entity could have and that impacts in the'
        ' type of operations and requirements they need.')

    l10n_py_vat = fields.Char(
        compute='_compute_l10n_py_vat', string="VAT", help='Computed field that returns VAT or nothing if this one'
        ' is not set for the partner')
    l10n_py_formatted_vat = fields.Char(
        compute='_compute_l10n_py_formatted_vat', string="Formatted VAT", help='Computed field that will convert the'
        ' given VAT number to the format {number:8}-{validation_number:1}')

    @api.depends('vat', 'l10n_latam_identification_type_id')
    def _compute_l10n_py_vat(self):
        """ We add this computed field that returns RUC (VAT PY) or nothing if this one is not set for the partner.
        This Validation can be also done by calling ensure_vat() method that returns the RUC (VAT PY) or error if this
        one is not found """
        recs_py_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.l10n_py_dnit_code == '0' and x.vat)
        for rec in recs_py_vat:
            rec.l10n_py_vat = stdnum.py.ruc.compact(rec.vat)
        remaining = self - recs_py_vat
        remaining.l10n_py_vat = False

    @api.depends('l10n_py_vat')
    def _compute_l10n_py_formatted_vat(self):
        """ This will add some dash to the RUC number (VAT PY) in order to show in his natural format:
        {number}-{validation_number} """
        recs_py_vat = self.filtered('l10n_py_vat')
        for rec in recs_py_vat:
            try:
                rec.l10n_py_formatted_vat = stdnum.py.ruc.format(rec.l10n_py_vat)
            except Exception as error:
                rec.l10n_py_formatted_vat = rec.l10n_py_vat
                _logger.error("Paraguayan VAT was not formatted: %s", repr(error))
        remaining = self - recs_py_vat
        remaining.l10n_py_formatted_vat = False

    ###
    ### Constraints
    ###
    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        """ Since we validate more documents than the vat for Paraguayan partners (RUC - VAT PY, CI) we
        extend this method in order to process it. """
        # NOTE by the moment we include the RUC (VAT PY) validation also here because we extend the messages
        # errors to be more friendly to the user. In a future when Odoo improve the base_vat message errors
        # we can change this method and use the base_vat.check_vat_py method.s
        l10n_py_partners = self.filtered(lambda p: p.l10n_latam_identification_type_id.l10n_py_dnit_code or p.country_code == 'PY')
        l10n_py_partners.l10n_py_identification_validation()
        return super(ResPartner, self - l10n_py_partners).check_vat()

    def l10n_py_identification_validation(self):
        for rec in self.filtered('vat'):
            try:
                module = rec._get_validation_module()
            except Exception as error:
                module = False
                _logger.error("Paraguayan document was not validated: %s (%s)",repr(error))

            if not module:
                continue
            try:
                module.validate(rec.vat)
            except module.InvalidChecksum:
                raise ValidationError(_('The validation digit is not valid for "%s" [%s]',
                                        rec.l10n_latam_identification_type_id.name,
                                        str(stdnum.py.ruc.calc_check_digit(self.vat))))
            except module.InvalidLength:
                raise ValidationError(_('Invalid length for "%s"', rec.l10n_latam_identification_type_id.name))
            except module.InvalidFormat:
                raise ValidationError(_('Only numbers allowed for "%s"', rec.l10n_latam_identification_type_id.name))
            except module.InvalidComponent:
                valid_cuit = ('20', '23', '24', '27', '30', '33', '34', '50', '51', '55')
                raise ValidationError(_('RUC number must be prefixed with one of the following: %s', ', '.join(valid_cuit)))
            except Exception as error:
                raise ValidationError(repr(error))

    def _get_validation_module(self):
        self.ensure_one()
        if self.l10n_latam_identification_type_id.l10n_py_dnit_code in ['0']:
            return stdnum.py.ruc
        #elif self.l10n_latam_identification_type_id.l10n_py_dnit_code == '1':
        #    return stdnum.py.ci

    ###
    ### Override
    ###
    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ['l10n_py_dnit_responsibility_type_id']

    ###
    ###
    ###
    def ensure_vat(self):
        """ This method is a helper that returns the VAT number is this one is defined if not raise an UserError.

        VAT is not mandatory field but for some Paraguayan operations the VAT is required, for eg  validate an
        electronic invoice, build a report, etc.

        This method can be used to validate is the VAT is proper defined in the partner """
        self.ensure_one()
        if not self.l10n_py_vat:
            raise UserError(_('No VAT configured for partner [%i] %s', self.id, self.name))
        return self.l10n_py_vat

    def _get_id_number_sanitize(self):
        """ Sanitize the identification number. Return the digits/integer value of the identification number
        If not vat number defined return 0 """
        self.ensure_one()
        if not self.vat:
            return 0
        if self.l10n_latam_identification_type_id.l10n_py_dnit_code in ['0']:
            # Compact is the number clean up, remove all separators leave only digits
            res = int(stdnum.py.ruc.compact(self.vat))
        else:
            id_number = re.sub('[^0-9]', '', self.vat)
            res = int(id_number)
        return res

    ###########################
    l10n_py_house = fields.Char("House")
    l10n_py_district_id = fields.Many2one("l10n_py_district")
    l10n_py_city_id = fields.Many2one("l10n_py_city")

    @api.onchange('country_id','l10n_py_city_id')
    def _onchange_city(self):
        if self.country_id.code == 'PY' and self.l10n_py_city_id.country_id.code == 'PY' :
            self.write({'city': self.l10n_py_city_id.name,})
            
    ###################
    @api.model
    def default_get(self,fields_list):
        res = super().default_get(fields_list)
        res.update(
            {'country_id':self.env['res.country'].search([('code', '=', 'PY')], limit=1).id}
        )
        res.update({'lang':self.env.lang})
        return res

        
    l10n_py_dnit_auth_code = fields.Char("Numero de Timbrado")
    l10n_py_dnit_auth_startdate = fields.Date("Fecha de Inicio del Timbrado")
    l10n_py_dnit_auth_enddate = fields.Date("Fecha de FIn del Timbrado")
    
    l10n_py_dnit_self_number = fields.Char("Nro de Constancia")
    l10n_py_dnit_self_control = fields.Char("Nro de Control")
    l10n_py_dnit_self_end_date = fields.Date("Fecha de Validez")
    
