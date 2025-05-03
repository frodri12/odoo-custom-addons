# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from random import randint
from datetime import datetime
from zoneinfo import ZoneInfo

import logging
import pytz
import json
import re
import requests
import os.path
from os import path

_logger = logging.getLogger(__name__)

_params = {}
_data = {}
_random_code = "0000000000"

class AccountMove(models.Model):

    _inherit = 'account.move'

    l10n_aipy_response_cdc = fields.Char(string='Response CDC', readonly=True, tracking=True, copy=False)
    
    l10n_aipy_response_codres = fields.Char(string='Response Code', readonly=True, tracking=True, copy=False)
    l10n_aipy_response_mesres = fields.Text(string='Response Message', readonly=True, tracking=True, copy=False)
    l10n_aipy_response_fecproc = fields.Datetime(string='Response Date', readonly=True, copy=False)

    l10n_aipy_request_json = fields.Text(string='Request JSON', readonly=True, copy=False)
    l10n_aipy_response_json = fields.Text(string='Response JSON', readonly=True, copy=False)

    #############################

    def _aipy_create_notification( self, title, type, body):
        message = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'type': type,
                'message': body,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
        return message

    def _aipy_get_url( self, key):
        sKey = 'aipy_edi.url.' + key + '.test' if self.company_id.l10n_aipy_testing_mode else '.prod'

        ICP = self.env['ir.config_parameter'].sudo()
        sRet = str(ICP.get_param(sKey))
        return sRet

    ### Convierte un string en formato 2019-03-01T10:23:53-03:00
    ### a un string UTC en formato 2019-03-01T13:23:53
    ### Solo esta soportado -03:00 y -04:00
    def _aipy_convert_date_to_utc(self, date):
        d1 = date.split("T")[0]
        d2 = date.split("T")[1]
        d3 = d2[8:]
        d2 = d2[0:8]
        tzname = 'UTC'
        if d3 == '-03:00':
            tzname = 'America/Buenos_Aires'
        elif d3 == '-04:00':
            tzname = 'America/Asuncion'
        dt = datetime.strptime(d1 + " " + d2, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(tzname))
        return dt.astimezone(ZoneInfo('UTC')).isoformat(timespec='seconds').replace("+00:00", "")

    #############################


    #############################
    def _aipy_initialize_data( self):
        _params = {}
        _data = {}

    def _aipy_setP( self, key, value):
        _params.update({ key : value })

    def _aipy_setD( self, key, value):
        _data.update({ key : value })

    #############################

    def _aipy_get_DateTimeFormat( self, date):
        return date.strftime("%Y-%m-%dT%H:%M:%S")

    def _aipy_get_NowTZ( self):
        now_time = datetime.now()
        user = self.env['res.users'].browse([2])
        tz = pytz.timezone(user.tz) or pytz.utc
        return pytz.utc.localize(now_time).astimezone(tz)

    #############################
    def _aipy_validate_random_code( self, code):
        acc = self.env['account.move'].search([('l10n_aipy_random_code', '=', code)])
        if len(acc) > 0:
            return True
        else:
            return False

    def _aipy_generate_random_code( self):
        pin_length = 9
        number_max = (10**pin_length) - 1
        number = randint( 0, number_max)
        delta = (pin_length - len(str(number))) * '0'
        _random_code = '%s%s' % (delta,number)
        
        condition = self._aipy_validate_random_code( _random_code)
        if condition:
            self._aipy_generate_random_code()
        self.l10n_aipy_random_code = _random_code
        return _random_code
    #############################

    def _aipy_compute_statement_lines( self):
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
            if ivaAmount == 0:
                ivaTipo = 3
            elif ivaBase != 100:
                ivaAmount = rec.tax_ids.amount * 100 / ivaBase
                ivaTipo = 4
            item.update({"ivaTipo": ivaTipo}) #E731
            item.update({"ivaBase": 0 if ivaTipo == 3 else ivaBase}) #E733
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
            self._aipy_setD("tipoTransaccion", tipoTransaccion) #D011
        self._aipy_setD("tipoImpuesto", globalTaxTye) #D013
        return items

    #############################
    def _aipy_compute_economic_activity( self):
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
            self._aipy_setP("actividadesEconomicas", ecos)
                
    #############################
    def _aipy_compute_estabecimientos( self):
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
                est.update({"email": email.split(",")[0]}) #D118
            else:
                est.update({"email": email}) #D118
        else:
            raise UserError(_("Email is required"))
        estabecimientos.append(est)
        return estabecimientos
                
    def _aipy_compute_regimeType( self):
        if self.company_id.l10n_aipy_regime_type_id:
            value = self.company_id.l10n_aipy_regime_type_id.code
            if value and value > 0:
                self._aipy_setP("tipoRegimen", value)
                
    #############################
    def _aipy_compute_timbrado( self):
        """
        Compute the timbrado number and date
        """
        auth_code = self.company_id.l10n_aipy_dnit_auth_code
        auth_date = self.company_id.l10n_aipy_dnit_auth_startdate
        if self.company_id.l10n_aipy_testing_mode:
            auth_code = self.company_id.l10n_aipy_dnit_auth_code_test
            auth_date = self.company_id.l10n_aipy_dnit_auth_startdate_test
        if not auth_code or not auth_date:
            raise UserError(_("Timbrado number and date are required"))
        if auth_code.__len__() != 8 and auth_code.__len__() != 11:
            raise UserError(_("Timbrado number must be 8 digits (12345678) or 11 digits (AA-12345678)"))
        if auth_code.__len__() == 8:
            self._aipy_setP("timbradoNumero", auth_code) #C004
        elif auth_code.__len__() == 11:
            if auth_code.split("-").__len__() != 2:
                raise UserError(_("Timbrado number must be 8 digits (12345678) or 11 digits (AA-12345678)"))
            self._aipy_setP("timbradoNumero", auth_code.split("-")[1]) #C004
            self._aipy_setP("numeroSerie", auth_code.split("-")[0]) #C010
        if auth_date:
            self._aipy_setP("timbradoFecha", auth_date.strftime("%Y-%m-%d")) #C008
        else:
            raise UserError(_("Timbrado date is required"))

    def _aipy_compute_digital_date( self):
        """
        Compute the digital date
        """
        now = datetime.now()
        user = self.env['res.users'].browse([2])
        tz = pytz.timezone(user.tz) or pytz.utc
        user_tz = pytz.utc.localize(now).astimezone(tz)
        return user_tz.strftime("%Y-%m-%dT%H:%M:%S") #A004

    def _aipy_compute_sequence_number( self):
        sequence_number = self.name
        if re.findall( "^\\d{3}-\\d{3}-\\d{7}$", sequence_number.split(" ")[1]) == 0:
            raise UserError(_("Sequence number format is invalid"))
        number = sequence_number.split(" ")[1]
        self._aipy_setD( "establecimiento", number.split("-")[0])
        self._aipy_setD( "punto", number.split("-")[1]) #C006
        self._aipy_setD( "numero", number.split("-")[2]) #C010

    def _aipy_compute_client( self):
        """
        Compute the client data
        """
        cliente = {}
        pais = self.partner_id.country_id.l10n_aipy_alpha_code
        departamento = self.partner_id.state_id.code
        distrito = self.partner_id.l10n_aipy_district_id.code
        ciudad = self.partner_id.l10n_aipy_city_id.code
        if self.partner_id.vat:
            if self.partner_id.l10n_latam_identification_type_id.l10n_aipy_dnit_code == "0" and pais == "PRY":
                cliente.update({"ruc": self.partner_id.vat}) #D206
                cliente.update({"contribuyente": True}) #D201
            else:
                cliente.update({"contribuyente": False}) #D201
                if pais == 'PRY':
                    cliente.update(
                        {"documentoTipo": self.partner_id.l10n_latam_identification_type_id.l10n_aipy_dnit_code}) #D208
                    cliente.update({"documentoNumero": self.partner_id.vat}) #D210
                else:
                    cliente.update({"documentoTipo": 9}) #D208
                    cliente.update({"documentoNumero": self.partner_id.vat}) #D210
                    cliente.update({"documentoTipoDescripcion": self.partner_id.l10n_latam_identification_type_id.name}) #D209

        if self.partner_id.l10n_latam_identification_type_id.l10n_aipy_dnit_code == "0":
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
                cliente.update({"tipoOperacion": 4}) #D202 B2F
                cliente.update({"tipoContribuyente": 2 if self.partner_id.is_company else 1}) #D205

        razonSocial = self.partner_id.name
        if razonSocial:
            cliente.update({"razonSocial": razonSocial}) #D211
        else:
            cliente.update({"razonSocial": "Sin Nombre"}) #D211

        # Direccion
        cliente.update({"pais": pais}) #D203
        if pais == 'PRY':
            if departamento and distrito and ciudad and pais == 'PRY':
                cliente.update({"departamento": departamento}) #D219
                cliente.update({"distrito": distrito}) #D221
                cliente.update({"ciudad": ciudad}) #D223
                cliente.update({"direccion": self.partner_id.street}) #D213
                cliente.update({"numeroCasa": self.partner_id.l10n_aipy_house if self.partner_id.l10n_aipy_house else 1}) #D218
            else:
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

    def _aipy_compute_factura( self):
        factura = {}
        factura.update({"presencia": 1}) #E011
        return factura

    def _aipy_compute_ncnd( self):
        ncnd = {}
        ncnd.update({"motivo": 2}) #E401
        return ncnd

    def _aipy_compute_remision( self):
        remision = {}
        remision.update({"motivo": 1}) #E501
        #remision.update({"tipoResponsable": 1}) #E503
        #remision.update({"kms": 1}) #E505
        #remision.update({"fechaFactura": 1}) #E506
        return remision

    def _aipy_compute_condicion( self):
        condicion = {}
        condicion.update({"tipo": 2}) #E601 Credito
        #
        credito = {}
        credito.update({"tipo": 1}) #E641
        credito.update({"plazo": "30 dias"}) #E643

        condicion.update({"credito": credito}) 
        return condicion

    def _aipy_compute_documentoAsociado( self):
        docAsoc = {}
        factura = self.reversed_entry_id
        if factura and factura.l10n_aipy_response_cdc and factura.l10n_aipy_response_cdc != None:
            docAsoc.update({"formato": 1}) #H002
            docAsoc.update({"cdc": factura.l10n_aipy_response_cdc}) #H004
        elif factura and factura.l10n_aipy_response_cdc == None:
            docAsoc.update({"formato": 2}) #H002
            tipo = factura.move_type
            if tipo == 'out_invoice':
                docAsoc.update({"tipo": 1}) #H009
            elif tipo == 'out_refund':
                docAsoc.update({"tipo": 2}) #H009
            elif tipo == 'out_receipt':
                docAsoc.update({"tipo": 4}) #H009
            elif tipo == 'in_refund':
                docAsoc.update({"tipo": 3}) #H009
            else:
                raise UserError(_("Document type is invalid (%s)" % tipo))
            docAsoc.update({"timbrado": factura.company_id.l10n_aipy_dnit_auth_code_test if factura.company_id.l10n_aipy_testing_mode else factura.company_id.l10n_aipy_dnit_auth_code}) #H005
            nroFactura = factura.name.split(" ")[1]
            docAsoc.update({"establecimiento": nroFactura.split("-")[0]}) #H006
            docAsoc.update({"punto": nroFactura.split("-")[1]}) #H007
            docAsoc.update({"numero": nroFactura.split("-")[2]}) #H008
        return docAsoc
    #############################

    def aipy_dnit_generate_json( self):
        """
        Generate the JSON file for the DNIT
        """
        # Initialize data
        self._aipy_initialize_data()
        # Set Params
        self._aipy_setP("version", 150) #AA002
        self._aipy_compute_timbrado()
        self._aipy_setP("ruc", self.company_id.vat) #D101
        self._aipy_setP("tipoContribuyente", 1 if self.company_id.partner_id.company_type == 'person' else 2) #D103
        self._aipy_compute_regimeType()
        self._aipy_setP("razonSocial", self.company_id.name) #D105
        if self.company_id.l10n_aipy_fantasy_name:
            self._aipy_setP("nombreFantasia", self.company_id.l10n_aipy_fantasy_name) #D106
        if self.company_id.l10n_aipy_testing_mode:
            self._aipy_setP("nombreFantasia", self.company_id.name)
            self._aipy_setP("razonSocial", "DE generado en ambiente de prueba - sin valor comercial ni fiscal") #D105
        self._aipy_setP("establecimientos", self._aipy_compute_estabecimientos())
        self._aipy_compute_economic_activity()

        # Set Data
        self._aipy_setD("fecha", self._aipy_compute_digital_date()) #A004
        self._aipy_setD("codigoSeguridadAleatorio", self._aipy_generate_random_code()) #B004
        self._aipy_setD("tipoEmision", 1 ) #B002
        tipoDocumento = self.move_type
        if tipoDocumento == 'out_invoice':
            self._aipy_setD("tipoDocumento", 1) #C002
        elif tipoDocumento == 'out_refund':
            self._aipy_setD("tipoDocumento", 5) #C002
        elif tipoDocumento == 'out_receipt':
            self._aipy_setD("tipoDocumento", 7) #C002
        elif tipoDocumento == 'in_refund':
            self._aipy_setD("tipoDocumento", 6) #C002
        else:
            raise UserError(_("Document type is invalid (%s)" % tipoDocumento))
        self._aipy_compute_sequence_number()
        #
        self._aipy_setD("moneda", self.currency_id.name) #D015
        if self.currency_id.name != 'PYG':
            self._aipy_setD("cambio", 1 / self.invoice_currency_rate) #D018
            self._aipy_setD("condicionTipoCambio", 1) #D017
        #
        self._aipy_setD("cliente", self._aipy_compute_client())
        if tipoDocumento == 'out_invoice':
            self._aipy_setD("factura", self._aipy_compute_factura())
            self._aipy_setD("condicion", self._aipy_compute_condicion())
        if tipoDocumento == 'in_refund' or tipoDocumento == 'out_refund':
            self._aipy_setD("notaCreditoDebito", self._aipy_compute_ncnd())
        if tipoDocumento == 'in_refund':
            self._aipy_setD("remision", self._aipy_compute_remision())
        #
        self._aipy_setD("items", self._aipy_compute_statement_lines())
        #
        if self.move_type == 'out_refund':
            self._aipy_setD("documentoAsociado", self._aipy_compute_documentoAsociado())
        #self._cr.commit()

        all = {}
        all.update({"empresa": self.company_id.vat.split("-")[0]})
        all.update({"servicio": "de"})
        all.update({"idCSC1": self.company_id.l10n_aipy_idcsc1_test if self.company_id.l10n_aipy_testing_mode else self.company_id.l10n_aipy_idcsc1_prod})
        all.update({"idCSC2": self.company_id.l10n_aipy_idcsc2_test if self.company_id.l10n_aipy_testing_mode else self.company_id.l10n_aipy_idcsc2_prod})
        all.update({"produccion": not self.company_id.l10n_aipy_testing_mode})
        all.update({"params": _params})
        all.update({"data": _data})
        self.l10n_aipy_request_json = json.dumps(all, indent=4)
        self.l10n_aipy_response_json = None
        self.l10n_aipy_response_cdc = None
        self.l10n_aipy_response_codres = None
        self.l10n_aipy_response_mesres = None
        self.l10n_aipy_response_fecproc = None

        #_logger.info( "\n -- JSON -- \n" + json.dumps(all, indent=4) + "\n")
        path_vscode_logs = "/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/logs"
        if path.exists(path_vscode_logs):
            with open(path_vscode_logs + '/params.json', 'w') as f:
                json.dump(_params, f, indent=4)
            with open(path_vscode_logs + '/data.json', 'w') as f:
                json.dump(_data, f, indent=4)

        #p = subprocess.run('/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/TestXML.sh', shell=True, capture_output=True, check=True, encoding='utf-8')

        #if p.stdout[0:5] == "<?xml":
        #    dom = xml.dom.minidom.parseString(p.stdout)
        #    pretty_xml_as_string = dom.toprettyxml()
        #    _logger.info( "\n\n" + pretty_xml_as_string)
        #    with open('/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/logs/response.xml', 'w') as f:
        #        f.write(pretty_xml_as_string)
        #else:
        #    _logger.info( "\n\n" + p.stdout)
        
        response = requests.post(
            self._aipy_get_url("recibe"),  json=json.loads(json.dumps(all)), allow_redirects=False)    
        if response.status_code == 301:
            response = requests.post( response.headers['Location'],  json=json.loads(json.dumps(all)))
        if response.status_code != 200:
            _logger.error( "Error: %s" % str(response.status_code))
            self.l10n_aipy_response_codres = str(response.status_code)
            self.l10n_aipy_response_mesres = response.text
            return self._aipy_create_notification( _('Error!'), 'danger', str(response.status_code) + " " + response.text)
        else:
            return self._aipy_json_responseDNIT(response)

    def _aipy_json_responseDNIT( self, response_data):
        """
        Process the response from the DNIT
        """
        response = response_data.json()
        self.l10n_aipy_response_json = json.dumps(response, indent=4)
        self.l10n_aipy_response_fecproc = datetime.now()
        if int(response['code']) != 0:
            self.l10n_aipy_response_status = 'E'
            self.l10n_aipy_response_codres = str(response['code'])
            self.l10n_aipy_response_mesres = response.get("message")
            msg = "Error: " + str(response['code']) + " " + str(response.get("message"))
            self.message_post(body=msg, message_type='notification')
            #self._cr.commit()
            #raise ValidationError(msg)
            return self._aipy_create_notification( _('Warining!'), 'warning', msg)

        rRetEnviDe = None
        payload = response.get("payload")
        if payload and payload != None:
            rRetEnviDe = payload.get("ns2:rRetEnviDe")

        rProtDe = None
        if rRetEnviDe and rRetEnviDe != None:
            rProtDe = rRetEnviDe.get("ns2:rProtDe")

        dId = None # l10n_aipy_response_cdc  Se guarda como esta
        dFecProc = None # l10n_aipy_response_fecproc  Convertir a UTC
        dEstRes = None # l10n_aipy_response_status "Aprobado":"A","Rechazado":"R",else:"AO"
        dProtAut = None # Por ahora no lo usamos
        gResProc = None
        if rProtDe and rProtDe != None:
            dId = rProtDe.get("ns2:Id")
            dFecProc = self._aipy_convert_date_to_utc(rProtDe.get("ns2:dFecProc"))
            dEstRes = rProtDe.get("ns2:dEstRes")
            dProtAut = rProtDe.get("ns2:dProtAut")
            gResProc = rProtDe.get("ns2:gResProc")

        dCodRes = None # l10n_aipy_response_codres  pasar a entero
        dMsgRes = None # l10n_aipy_response_mesres  Se guarda como esta
        if gResProc and gResProc != None and str(type(gResProc)) == "<class 'dict'>":
            dCodRes = gResProc.get("ns2:dCodRes")
            dMsgRes = gResProc.get("ns2:dMsgRes")
        elif gResProc and gResProc != None and str(type(gResProc)) == "<class 'list'>":
            for rec in gResProc:
                dCodRes = rec.get("ns2:dCodRes")
                dMsgRes = rec.get("ns2:dMsgRes")

        if dId != None:
            self.l10n_aipy_response_cdc = dId
        if dFecProc != None:
            self.l10n_aipy_response_fecproc = datetime.strptime(dFecProc, "%Y-%m-%dT%H:%M:%S")           
                    
        if dEstRes != None:
            if dEstRes == "Aprobado":
                self.l10n_aipy_response_status = 'A'
            elif dEstRes == "Rechazado":
                self.l10n_aipy_response_status = 'R'
            else:
                self.l10n_aipy_response_status = 'O'
        if dCodRes != None:
            self.l10n_aipy_response_codres = dCodRes
        if dMsgRes != None:
            self.l10n_aipy_response_mesres = dMsgRes
                    
        if dEstRes == None or dEstRes == "Rechazado":
            msg = "Warning: Documento " + str(dEstRes) + "\n[" + str(dCodRes) + "-" + str(dMsgRes) + "] "
            return self._aipy_create_notification( _('Warining!'), 'info', msg)

        if dEstRes[:1] == "A":
            msg = "Success: Documento " + str(dEstRes) + "\n[" + str(dCodRes) + "-" + str(dMsgRes) + "] "
            return self._aipy_create_notification( _('Success!'), 'info', msg)


        