# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from random import randint
from datetime import datetime

import logging
import pytz
import json
import re
import subprocess

_logger = logging.getLogger(__name__)

_params = {}
_data = {}

class AccountMove(models.Model):

    _inherit = 'account.move'

    #############################
    def _initialize_data( self):
        _params = {}
        _data = {}

    def _setP( self, key, value):
        _params.update({ key : value })

    def _setD( self, key, value):
        _data.update({ key : value })

    #############################

    def _get_DateTimeFormat( self, date):
        return date.strftime("%Y-%m-%dT%H:%M:%S")

    def _get_NowTZ( self):
        now_time = datetime.now()
        user = self.env['res.users'].browse([2])
        tz = pytz.timezone(user.tz) or pytz.utc
        return pytz.utc.localize(now_time).astimezone(tz)

    #############################
    def _validate_random_code( self, code):
        acc = self.env['account.move'].search([('l10n_aipy_random_code', '=', code)])
        if len(acc) > 0:
            return True
        else:
            return False

    def _generate_random_code( self):
        pin_length = 9
        number_max = (10**pin_length) - 1
        number = randint( 0, number_max)
        delta = (pin_length - len(str(number))) * '0'
        random_code = '%s%s' % (delta,number)
        condition = self._validate_random_code( random_code)
        if condition:
            self._generate_random_code()
        l10n_aipy_random_code = random_code
        return random_code
    #############################

    def _compute_statement_lines( self):
        items = []
        isService = False
        isProduct = False
        globalTaxTye = "0"
        for rec in self.invoice_line_ids:
            productId =rec.product_id
            uomId = productId.uom_id
            item = {}
            item.update({"codigo": productId.default_code if productId.default_code else productId.id}) #E701
            item.update({"descripcion": productId.name}) #E708
            if uomId.l10n_aipy_dnit_code:
                item.update({"unidadMedida": uomId.l10n_aipy_dnit_code}) #E709
            item.update({"cantidad": rec.quantity}) #E711
            # E8 E704-E707 - Pendiente de implementar
            item.update({"pais": "PRY"}) #E712
            item.update({"observacion": productId.name}) #E714
            # E8 E715-E719 - Pendiente de implementar
            item.update({"precioUnitario": rec.price_unit}) #E721
            if self.currency_id.name != 'PYG':
                item.update({"cambio": 1 / rec.currency_rate}) #E725
            # E8.1.1 EA001-EA007 - Pendiente de implementar
            ivaTipo = 1
            ivaBase = rec.tax_ids.l10n_aipy_tax_base
            ivaAmount = rec.tax_ids.amount
            if ivaBase != 100:
                ivaAmount = rec.tax_ids.amount * 100 / ivaBase
                ivaTipo = 4
            if ivaAmount == 0:
                ivaTipo = 3
            item.update({"ivaTipo": ivaTipo}) #E731
            item.update({"ivaBase": ivaBase}) #E733
            item.update({"iva": ivaAmount}) #E734
            # E8.4 E750-E760 - Pendiente de implementar
            # E8.5 E770-E789 - Pendiente de implementar
            #
            taxType = rec.tax_ids.l10n_aipy_tax_type
            if globalTaxTye == "0":
                globalTaxTye = taxType
            elif globalTaxTye == "5":
                if taxType == "2":
                    globalTaxTye = "2"
            elif globalTaxTye == "4":
                globalTaxTye = taxType
            elif globalTaxTye == "3":
                if taxType == "1" or taxType == "5":
                    globalTaxTye = "5"
                elif taxType == "2":
                    globalTaxTye = "2"
            elif globalTaxTye == "1":
                if taxType == "3" or taxType == "5":
                    globalTaxTye = "5"
                elif taxType == "2":
                    globalTaxTye = "2"

            #
            if productId.type == 'combo':
                isService = True
                isProduct = True
            if productId.type == 'service':  # consu, service, combo
                isService = True
            if productId.type == 'consu':
                isProduct = True

            items.append(item)

        tipoTransaccion = 0
        if isService and isProduct:
            tipoTransaccion = 3
        elif isService:
            tipoTransaccion = 2
        else:
            tipoTransaccion = 1
        if self.move_type == 'out_invoice' and tipoTransaccion != 0:
            self._setD("tipoTransaccion", tipoTransaccion) #D011
        self._setD("tipoImpuesto", globalTaxTye) #D013
        return items

    #############################
    def _compute_economic_activity( self):
        ecos = []
        ecos_count = 0
        for rec in self.company_id.l10n_aipy_economic_activity_ids:
            eco = {}
            eco.update({"codigo": rec.code}) #D131
            eco.update({"descripcion": rec.name}) #D132
            ecos.append(eco)
            ecos_count += 1
        if ecos_count == 0:
            raise UserError(_("Economic activity is required"))
        else:
            self._setP("actividadesEconomicas", ecos)
                
    #############################
    def _compute_estabecimientos( self):
        estabecimientos = []
        est = {}
        est.update({"codigo": "%03d" % int(self.company_id.l10n_aipy_dnit_organization)})
        est.update({"direccion": self.company_id.street}) #D107
        est.update(
            {"numeroCasa": self.company_id.l10n_aipy_house if self.company_id.l10n_aipy_house else 0}) #D108
        if self.company_id.street2:
            est.update({"complementoDireccion1": self.company_id.street2}) #D109
        est.update({"departamento": int(self.company_id.state_id.code)}) #D111
        est.update({"distrito": int(self.company_id.l10n_aipy_district_id.code)}) #D113
        est.update({"ciudad": int(self.company_id.l10n_aipy_city_id.code)}) #D115
        telefono = self.company_id.phone
        if telefono:
            if telefono.__len__() < 6 or telefono.__len__() > 15:
                raise UserError(_("Phone number must be between 6 and 15 digits"))
            else:
                est.update({"telefono": telefono}) #D117
        else:
            raise UserError(_("Phone number is required"))
        email = self.company_id.email
        if email:
            if email.find(",") > -1:
                est.update({"email": email.splat(",")[0]}) #D118
            else:
                est.update({"email": email}) #D118
        else:
            raise UserError(_("Email is required"))
        estabecimientos.append(est)
        return estabecimientos
                
    def _compute_regimeType( self):
        if self.company_id.l10n_aipy_regime_type_id:
            value = self.company_id.l10n_aipy_regime_type_id.code
            if value and value > 0:
                self._setP("tipoRegimen", value)
                
    #############################
    def _compute_timbrado( self):
        """
        Compute the timbrado number and date
        """
        auth_code = self.company_id.l10n_aipy_dnit_auth_code
        auth_date = self.company_id.l10n_aipy_dnit_auth_date
        if self.company_id.l10n_aipy_testing_mode:
            auth_code = self.company_id.l10n_aipy_dnit_auth_code_test
            auth_date = self.company_id.l10n_aipy_dnit_auth_date_test
        if not auth_code or not auth_date:
            raise UserError(_("Timbrado number and date are required"))
        if auth_code.__len__() != 8 and auth_code.__len__() != 11:
            raise UserError(_("Timbrado number must be 8 digits (12345678) or 11 digits (AA-12345678)"))
        if auth_code.__len__() == 8:
            self._setP("timbradoNumero", auth_code) #C004
        elif auth_code.__len__() == 11:
            if auth_code.split("-").__len__() != 2:
                raise UserError(_("Timbrado number must be 8 digits (12345678) or 11 digits (AA-12345678)"))
            self._setP("timbradoNumero", auth_code.split("-")[1]) #C004
            self._setP("numeroSerie", auth_code.split("-")[0]) #C010
        if auth_date:
            self._setP("timbradoFecha", auth_date.strftime("%Y-%m-%d")) #C008
        else:
            raise UserError(_("Timbrado date is required"))

    def _compute_digital_date( self):
        """
        Compute the digital date
        """
        now = datetime.now()
        user = self.env['res.users'].browse([2])
        tz = pytz.timezone(user.tz) or pytz.utc
        user_tz = pytz.utc.localize(now).astimezone(tz)
        return user_tz.strftime("%Y-%m-%dT%H:%M:%S") #A004

    def _compute_sequence_number( self):
        sequence_number = self.name
        if re.findall( "^\\d{3}-\\d{3}-\\d{7}$", sequence_number.split(" ")[1]) == 0:
            raise UserError(_("Sequence number format is invalid"))
        number = sequence_number.split(" ")[1]
        self._setD( "establecimiento", number.split("-")[0])
        self._setD( "punto", number.split("-")[1]) #C006
        self._setD( "numero", number.split("-")[2]) #C010

    def _compute_client( self):
        """
        Compute the client data
        """
        cliente = {}
        pais = self.partner_id.country_id.l10n_aipy_alpha_code
        departamento = self.partner_id.state_id.code
        distrito = self.partner_id.l10n_aipy_district_id.code
        ciudad = self.partner_id.l10n_aipy_city_id.code
        if self.partner_id.vat:
            if self.partner_id.l10n_latam_identification_type_id.l10n_aipy_dnit_code == 0 and pais == "PRY":
                cliente.update({"ruc": self.partner_id.vat}) #D206
                cliente.update({"contribuyente": True}) #D201
            else:
                cliente.update({"contribuyente": False}) #D201
                if pais == 'PRY':
                    cliente.update(
                        {"documentoTipo": self.partner_id.l10n_latam_identification_type_id.l10n_aipy_dnit_code}) #D208
                    cliente.update({"documentoNumero": self.partner_id.vat}) #D210

        if self.partner_id.l10n_latam_identification_type_id.l10n_aipy_dnit_code == 0:
            if self.partner_id.is_company:
                cliente.update({"tipoOperacion": 1}) #D202 B2B
                cliente.update({"tipoContribuyente": 2}) #D205 Persona Juridica
            else:
                cliente.update({"tipoOperacion": 2}) #D202 B2C
                cliente.update({"tipoContribuyente": 1}) #D205 Persona Fisica
            if self.partner_id.country_id.code != 'PY':
                cliente.update({"tipoOperacion": 4}) #D202 B2F
        else:
            if self.partner_id.country_id.code == 'PY':
                cliente.update({"tipoOperacion": 2}) #D202 B2C
                cliente.update({"tipoContribuyente": 1}) #D205 Persona Fisica
            else:
                cliente.update({"tipoOperacion": 2}) #D202 B2F
                cliente.update({"tipoContribuyente": 2 if self.partner_id.is_company else 1}) #D205

        razonSocial = self.partner_id.name
        if razonSocial:
            cliente.update({"razonSocial": razonSocial}) #D211
        else:
            cliente.update({"razonSocial": "Sin Nombre"}) #D211

        # Direccion
        cliente.update({"pais": pais}) #D203
        if departamento and distrito and ciudad and pais == 'PRY':
            cliente.update({"departamento": departamento}) #D219
            cliente.update({"distrito": distrito}) #D221
            cliente.update({"ciudad": ciudad}) #D223
            cliente.update({"direccion": self.partner_id.street}) #D213
            cliente.update({"numeroCasa": self.partner_id.l10n_aipy_house if self.partner_id.l10n_aipy_house else 0}) #D218
        else:
            cliente.update({"direccion": self.partner_id.street}) #D213
            cliente.update({"numeroCasa": self.partner_id.l10n_aipy_house if self.partner_id.l10n_aipy_house else 0}) #D218
        if self.partner_id.phone:
            cliente.update({"telefono": self.partner_id.phone}) #D214
        if self.partner_id.mobile:
            cliente.update({"celular": self.partner_id.mobile}) #D215
        if self.partner_id.email:
            cliente.update({"email": self.partner_id.email}) #D215
        return cliente

    def _compute_factura( self):
        factura = {}
        factura.update({"presencia": 1}) #E011
        return factura

    def _compute_ncnd( self):
        ncnd = {}
        ncnd.update({"motivo": 2}) #E401
        return ncnd

    def _compute_remision( self):
        remision = {}
        remision.update({"motivo": 1}) #E501
        #remision.update({"tipoResponsable": 1}) #E503
        #remision.update({"kms": 1}) #E505
        #remision.update({"fechaFactura": 1}) #E506
        return remision

    def _compute_condicion( self):
        condicion = {}
        condicion.update({"tipo": 2}) #E601 Credito
        #
        credito = {}
        credito.update({"tipo": 1}) #E641
        credito.update({"plazo": "30 dias"}) #E643

        condicion.update({"credito": credito}) 
        return condicion

    #############################


    def dnit_generate_json( self):
        """
        Generate the JSON file for the DNIT
        """
        # Initialize data
        self._initialize_data()
        # Set Params
        self._setP("version", 150) #AA002
        self._compute_timbrado()
        self._setP("ruc", self.company_id.vat) #D101
        self._setP("tipoContribuyente", 1 if self.company_id.partner_id.company_type == 'person' else 2) #D103
        self._compute_regimeType()
        self._setP("razonSocial", self.company_id.name) #D105
        if self.company_id.l10n_aipy_fantasy_name:
            self._setP("nombreFantasia", self.company_id.l10n_aipy_fantasy_name) #D106
        if self.company_id.l10n_aipy_testing_mode:
            self._setP("nombreFantasia", self.company_id.name)
            self._setP("razonSocial", "DE generado en ambiente de prueba - sin valor comercial ni fiscal") #D105
        self._setP("establecimientos", self._compute_estabecimientos())
        self._compute_economic_activity()

        # Set Data
        self._setD("fecha", self._compute_digital_date()) #A004
        self._setD("codigoSeguridadAleatorio", self._generate_random_code()) #B004
        self._setD("tipoEmision", 1 ) #B002
        tipoDocumento = self.move_type
        if tipoDocumento == 'out_invoice':
            self._setD("tipoDocumento", 1) #C002
        elif tipoDocumento == 'out_refund':
            self._setD("tipoDocumento", 5) #C002
        elif tipoDocumento == 'out_receipt':
            self._setD("tipoDocumento", 7) #C002
        elif tipoDocumento == 'in_refund':
            self._setD("tipoDocumento", 6) #C002
        else:
            raise UserError(_("Document type is invalid (%s)" % tipoDocumento))
        self._compute_sequence_number()
        #
        self._setD("moneda", self.currency_id.name) #D015
        if self.currency_id.name != 'PYG':
            self._setD("cambio", 1 / self.invoice_currency_rate) #D018
            self._setD("condicionTipoCambio", 1) #D017
        #
        self._setD("cliente", self._compute_client())
        if tipoDocumento == 'out_invoice':
            self._setD("factura", self._compute_factura())
            self._setD("condicion", self._compute_condicion())
        if tipoDocumento == 'in_refund' or tipoDocumento == 'out_refund':
            self._setD("notaCreditoDebito", self._compute_ncnd())
        if tipoDocumento == 'in_refund':
            self._setD("remision", self._compute_remision())
        #
        self._setD("items", self._compute_statement_lines())
        #
        _logger.info( "----- JSON PARAMS ----")
        _logger.warning( "\n -- PARAMS -- \n" + json.dumps(_params, indent=4) + "\n")
        _logger.info( "----- JSON DATA ----")
        _logger.warning( "\n -- DATA -- \n" + json.dumps(_data, indent=4) + "\n")
        with open('/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/params.json', 'w') as f:
            json.dump(_params, f, indent=4)
        with open('/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/data.json', 'w') as f:
            json.dump(_data, f, indent=4)
        p = subprocess.run('/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/TestXML.sh', shell=True, capture_output=True, check=True, encoding='utf-8')
        _logger.warning( "\n\n" + p.stdout)