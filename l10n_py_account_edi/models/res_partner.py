# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

import re
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):

    _inherit = 'res.partner'


    def _get_l10n_py_dnit_ws_cliente( self):
        cliente = {}
        pais = self.country_id.l10n_py_alpha_code
        departamento = self.state_id.code
        distrito = self.l10n_py_district_id.code
        ciudad = self.l10n_py_city_id.code
        if self.vat:
            if self.l10n_latam_identification_type_id.l10n_py_dnit_code == "0" and pais == "PRY":
                cliente.update({"ruc": self.vat}) #D206
                cliente.update({"contribuyente": True}) #D201
            else:
                cliente.update({"contribuyente": False}) #D201
                if pais == 'PRY':
                    cliente.update({"documentoTipo": self.l10n_latam_identification_type_id.l10n_py_dnit_code}) #D208
                    cliente.update({"documentoNumero": self.vat}) #D210
                else:
                    cliente.update({"documentoTipo": 9}) #D208
                    cliente.update({"documentoNumero": self.vat}) #D210
                    cliente.update({"documentoTipoDescripcion": self.l10n_latam_identification_type_id.name}) #D209

        if self.l10n_latam_identification_type_id.l10n_py_dnit_code == "0":
            if self.is_company:
                cliente.update({"tipoOperacion": 1}) #D202 B2B
                cliente.update({"tipoContribuyente": 2}) #D205 Persona Juridica
            else:
                cliente.update({"tipoOperacion": 2}) #D202 B2C
                cliente.update({"tipoContribuyente": 1}) #D205 Persona Fisica
                if self.country_id.code != 'PY':
                    cliente.update({"tipoOperacion": 4}) #D202 B2F
        else:
            if self.country_id.code == 'PY':
                cliente.update({"tipoOperacion": 2}) #D202 B2C
                cliente.update({"tipoContribuyente": 1}) #D205 Persona Fisica
            else:
                cliente.update({"tipoOperacion": 4}) #D202 B2F
                cliente.update({"tipoContribuyente": 2 if self.is_company else 1}) #D205

        cliente.update({"razonSocial": self.name if self.name else "Sin Nombre"}) #D211

        cliente.update({"pais": pais}) #D203
        if pais == 'PRY':
            if departamento and distrito and ciudad and pais == 'PRY':
                cliente.update({"departamento": departamento}) #D219
                cliente.update({"distrito": distrito}) #D221
                cliente.update({"ciudad": ciudad}) #D223
                cliente.update({"direccion": self.street}) #D213
                cliente.update({"numeroCasa": self.l10n_py_house if self.l10n_py_house else 1}) #D218
            else:
                cliente.update({"direccion": self.street}) #D213
                cliente.update({"numeroCasa": self.l10n_py_house if self.l10n_py_house else 0}) #D218
        else:
            cliente.update({"direccion": self.street}) #D213
            cliente.update({"numeroCasa": self.l10n_py_house if self.l10n_py_house else 0}) #D218
        if self.phone:
            cliente.update({"telefono": re.sub('[^0-9]', '', self.phone)}) #D214
        if self.mobile:
            cliente.update({"celular": re.sub('[^0-9]', '', self.mobile)}) #D215
        if self.email:
            cliente.update({"email": self.email}) #D215
        return cliente
