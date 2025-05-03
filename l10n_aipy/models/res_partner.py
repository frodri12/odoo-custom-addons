# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import ValidationError, UserError

import logging
import re
import stdnum.py

_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = (
    'street', 'l10n_aipy_house', 'street2', 
    'zip', 'city', 'state_id', 'l10n_aipy_district_id', 
    'l10n_aipy_city_id', 'country_id')

class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_aipy_house = fields.Char("House")
    l10n_aipy_district_id = fields.Many2one("l10n_aipy_district")
    l10n_aipy_city_id = fields.Many2one("l10n_aipy_city")

    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type',
        string="Identification Type", index='btree_not_null', auto_join=True,
        default=lambda self: self.env.ref('l10n_aipy.it_ruc', raise_if_not_found=False),
        help="The type of identification")

    l10n_aipy_dnit_auth_code = fields.Char("Numero de Timbrado")
    l10n_aipy_dnit_auth_startdate = fields.Date("Fecha de Inicio del Timbrado")
    l10n_aipy_dnit_auth_enddate = fields.Date("Fecha de FIn del Timbrado")
    
    @api.model
    def default_get(self,fields_list):
        res = super().default_get(fields_list)
        res.update(
            {'country_id':self.env['res.country'].search([('code', '=', 'PY')], limit=1).id}
        )
        res.update({'lang':self.env.lang})
        return res

    @api.onchange('country_id','l10n_aipy_city_id')
    def _onChange_City(self):
        if self.country_id.code == 'PY' and self.l10n_aipy_city_id.country_id.code == 'PY' :
            self.write({'city': self.l10n_aipy_city_id.name,})

    @api.constrains('vat', 'l10n_latam_identification_type_id')
    def check_vat(self):
        if self.env.context.get('no_vat_validation'):
            return
        if not self.vat:
            return
        #with_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.is_vat)
        if self.commercial_partner_id.country_id.code == 'PY' and self.l10n_latam_identification_type_id.name == 'RUC':
            ## Validar
            if re.findall("^[0-9]{5,8}-[0-9]$", self.vat).__len__() == 0:
                #raise ValidationError("El formato del RUC es incorrecto [XXXXX-X, XXXXXX-X, XXXXXXX-X or XXXXXXXX-X]")
                raise ValidationError( _("The %(vat_label)s number [%(wrong_vat)s] does not seem to be valid.\nNote: the expected format is: %(expected_format)s",
                vat_label=self.l10n_latam_identification_type_id.name,
                wrong_vat=self.vat,
                expected_format="XXXXX-X, XXXXXX-X, XXXXXXX-X o XXXXXXXX-X")
                )
            else:
                # Validar el digito verificador
                sRUC = self.vat.split('-')
                sDigit = stdnum.py.vat.calc_check_digit(sRUC[0])
                if sRUC[1] != str(sDigit):
                    raise ValidationError( _("The %(vat_label)s number [%(wrong_vat)s] does not seem to be valid.\nNote: the expected format is: %(expected_format)s\nThe verification digit is %(sDigit)s",
                    vat_label=self.l10n_latam_identification_type_id.name,
                    wrong_vat=self.vat,
                    expected_format="XXXXX-X, XXXXXX-X, XXXXXXX-X o XXXXXXXX-X",
                    sDigit=sDigit)
                    )

