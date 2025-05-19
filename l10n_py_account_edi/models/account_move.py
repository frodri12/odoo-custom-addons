# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
from datetime import datetime
import json
import os.path
from os import path
import requests

from . import libpydate
from . import libpyrandom
from . import libpyaccount
from . import libpydnitws


_logger = logging.getLogger(__name__)

_params = {}
_data = {}

class AccountMove(models.Model):

    _inherit = "account.move"

    l10n_py_dnit_cdc = fields.Char('Authorization Code', copy=False, size=44, 
         help="Paraguay: authorization code given by DNIT after electronic invoice is created and valid.")

    l10n_py_dnit_ws_response_cdc = fields.Char(string="CDC", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_fecproc = fields.Char(string="Fecha de procesado", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_digval = fields.Char(string="Digito de verificacion", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_estres = fields.Selection(selection=[
            ('P', 'Pending'),('E', 'Error'),('A', 'Aproved'),
            ('O', 'Aproved with Observations'),('R', 'Rejected'),
        ], string='DNIT Status', default='P', readonly=True,tracking=True, copy=False)
    
    l10n_py_dnit_ws_response_protaut  = fields.Char(string="Protocolo de autorizacion", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_codres = fields.Char(string="Codigo de respuesta", readonly=True, tracking=True, copy=False)
    l10n_py_dnit_ws_response_msgres = fields.Char(string="Mensaje de respuesta", readonly=True, tracking=True, copy=False)

    l10n_py_dnit_ws_request_json = fields.Text(string="JSON de envio", readonly=True, copy=False)
    l10n_py_dnit_ws_request_xml = fields.Text(string="XML de envio", readonly=True, copy=False)
    l10n_py_dnit_ws_response_json = fields.Text(string="JSON de respuesta", readonly=True, copy=False)

    l10n_py_dnit_ws_random_code = fields.Char(string='Random Code', readonly=True, store=True, index = True,tracking=True, copy=False)

    def _get_l10n_py_ws_dnit_document_asociado( self):
        docAsoc = {}
        factura = self.reversed_entry_id
        if factura and factura.l10n_py_dnit_ws_response_cdc and factura.l10n_py_dnit_ws_response_cdc != None:
            docAsoc.update({"formato": 1}) #H002
            docAsoc.update({"cdc": factura.l10n_py_dnit_ws_response_cdc}) #H004
        elif factura and factura.l10n_py_dnit_ws_response_cdc == None:
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
            docAsoc.update({"timbrado": factura.journal_id.l10n_py_dnit_timbrado}) #H005
            nroFactura = factura.l10n_latam_document_number
            docAsoc.update({"establecimiento": nroFactura.split("-")[0]}) #H006
            docAsoc.update({"punto": nroFactura.split("-")[1]}) #H007
            docAsoc.update({"numero": nroFactura.split("-")[2]}) #H008
        return docAsoc

    def _get_l10n_py_dnit_ws_url( self, key):
        sKey = 'l10n_py_edi.url.' + key + '.test' if self.company_id.l10n_py_dnit_ws_environment == 'testing' else '.prod'

        ICP = self.env['ir.config_parameter'].sudo()
        sRet = str(ICP.get_param(sKey))
        return sRet


    # Prepare Request Data for webservices. Generate the JSON file for the DNIT
    def _prepare_l10n_py_ws_data( self):
        _params = {}
        _data = {}
        # Set Params
        _params.update({ "version" : 150 }) #AA002
        _params.update({ "ruc" : self.company_id.vat }) #D101
        _params.update({ "tipoContribuyente" : 2 if self.company_id.partner_id.is_company else 1 }) #D103
        _params.update({ "razonSocial" : self.company_id.name }) #D105
        if self.company_id.l10n_py_dnit_ws_environment == 'testing':
            _params.update({ "nombreFantasia" : self.company_id.name }) #D106
            _params.update({ "razonSocial" : "DE generado en ambiente de prueba - sin valor comercial ni fiscal" }) #D105
        _params.update({ "establecimientos" : self.company_id._get_l10n_py_dnit_ws_establecimiento() }) #AA002
        _params.update({ "actividadesEconomicas" : self.company_id._get_l10n_py_dnit_ws_economic_activities() }) #AA002

        timbrado = self.journal_id._get_l10n_py_dnit_ws_timbrado(self.company_id)
        _params.update({ "timbradoNumero" : timbrado.get('timbradoNumero') }) #C004
        _params.update({ "timbradoFecha" : timbrado.get('timbradoFecha') }) #C008
        if timbrado.get('numeroSerie') != None:
            _params.update({ "numeroSerie" : timbrado.get('numeroSerie') }) #C010
        if self.company_id.l10n_py_regime_type_id:
            value = self.company_id.l10n_py_regime_type_id.code
            if value and value > 0:
                _params.update({ "tipoRegimen" : value }) 

        _data.update({ "fecha" : libpydate.from_date2tz(self, datetime.now()).strftime("%Y-%m-%dT%H:%M:%S") }) #A004
        _data.update({ "codigoSeguridadAleatorio" : libpyrandom.generate_random_code(self)}) #B004
        _data.update({ "tipoEmision" : 1}) #B002
        _data.update({ "tipoDocumento" : libpyaccount.get_tipoDocumento(self.move_type)}) #C002
        _data.update({ "establecimiento" : self.l10n_latam_document_number.split("-")[0]}) 
        _data.update({ "punto" : self.l10n_latam_document_number.split("-")[1]}) #C006
        _data.update({ "numero" : self.l10n_latam_document_number.split("-")[2]}) #C010
        _data.update({ "moneda" : self.currency_id.name}) #D015
        if self.currency_id.name != 'PYG':
            _data.update({ "cambio" : 1 / self.invoice_currency_rate}) #D018
            _data.update({ "condicionTipoCambio" : 1}) #D017
        _data.update({ "cliente" : self.partner_id._get_l10n_py_dnit_ws_cliente()}) 
        if self.move_type == 'out_invoice':
            _data.update({ "factura" : libpyaccount.get_factura()}) #E010
            _data.update({ "condicion" : libpyaccount.get_condicion_operacion(self.invoice_date, self.invoice_date_due)}) 
        elif self.move_type == 'out_refund':
            _data.update({ "notaCreditoDebito" : libpyaccount.get_motivo_nce(self.ref)}) 
            _data.update({ "documentoAsociado" : self._get_l10n_py_ws_dnit_document_asociado()}) 
        ## Queda pendiente de analisis
        #elif self.move_type == 'out_receipt':
            ## Recibos a clientes
        elif self.move_type == 'in_invoice':
            ## Solo para autofactura
            return 4
        elif self.move_type == 'in_refund':
            _data.update({ "notaCreditoDebito" : libpyaccount.get_motivo_nce(self.ref)}) 
        else:
            raise UserError(_("Document type is invalid (%s)" % self.move_type))
        ## Items
        items = []
        isService = False
        isProduct = False
        globalTaxTye = "0"
        for rec in self.invoice_line_ids:
            if rec.display_type == "product":
                items.append(rec._get_l10n_py_dnit_ws_item())
                if rec.product_id.type == 'combo':
                    isProduct = True
                if rec.product_id.type == 'service':  # consu, service, combo
                    isService = True
                if rec.product_id.type == 'consu':
                    isProduct = True
                taxType = rec.tax_ids.l10n_py_tax_type
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
        _data.update({ "items" : items})
        tipoTransaccion = 0
        if isService and isProduct:
            tipoTransaccion = 3
        elif isService:
            tipoTransaccion = 2
        else:
            tipoTransaccion = 1
        if self.move_type == 'out_invoice' and tipoTransaccion != 0:
            _data.update({ "tipoTransaccion" : tipoTransaccion}) #D011
        _data.update({ "tipoImpuesto" : globalTaxTye})
        all = {}
        all.update({"empresa": self.company_id.vat.split("-")[0]})
        all.update({"servicio": "de"})
        #all.update({"idCSC1": self.company_id.l10n_aipy_idcsc1_test if self.company_id.l10n_aipy_testing_mode else self.company_id.l10n_aipy_idcsc1_prod})
        #all.update({"idCSC2": self.company_id.l10n_aipy_idcsc2_test if self.company_id.l10n_aipy_testing_mode else self.company_id.l10n_aipy_idcsc2_prod})
        #all.update({"produccion": not self.company_id.l10n_aipy_testing_mode})
        all.update({"params": _params})
        all.update({"data": _data})
        _logger.error("All JSON Data: \n%s\n", json.dumps(all, indent=4))
        path_vscode_logs = "/opt/Odoo/odoo-18.0.developer/odoo-custom-addons/.vscode/logs"
        if path.exists(path_vscode_logs):
            with open(path_vscode_logs + '/params.json', 'w') as f:
                json.dump(_params, f, indent=4)
            with open(path_vscode_logs + '/data.json', 'w') as f:
                json.dump(_data, f, indent=4)
        return all

    # Buttons
    def _post(self, soft=True):
        py_invoices = self.filtered(lambda x: x.is_invoice() and x.country_code == "PY")
        sale_py_invoices = py_invoices.filtered(lambda x: x.move_type in ['out_invoice', 'out_refund'])

        # Verify only Vendor bills (only when verification is configured as 'required')
        #(py_invoices - sale_py_invoices)._l10n_ar_check_afip_auth_verify_required()

        # Send invoices to DNIT and get the return info
        py_edi_invoices = py_invoices.filtered(lambda x: x.journal_id.l10n_py_dnit_pos_system in ('RLI_RLM','AURLI_RLM','BFERCEL','FEERCEL','CPERCEL'))
        validated = error_invoice = self.env['account.move']
        for inv in py_edi_invoices:

            validated += super(AccountMove, inv)._post(soft=soft)

            _logger.error("Partner: %s Documento: %s", inv.partner_id.name, inv.l10n_latam_document_number)
            ### La llamada a la SET
            #return_info = inv._l10n_ar_do_afip_ws_request_cae(client, auth, transport)
            return_info = inv._l10n_py_do_dnit_ws_request()
            if return_info:
                error_invoice = inv
                validated -= inv
                break

            # If we get CAE from AFIP then we make commit because we need to save the information returned by AFIP
            # in Odoo for consistency, this way if an error ocurrs later in another invoice we will have the ones
            # correctly validated in AFIP in Odoo (CAE, Result, xml response/request).
            if not self.env.context.get('l10n_py_invoice_skip_commit'):
                self._cr.commit()

        if error_invoice:
            if error_invoice.exists():
                msg = _('We couldn\'t validate the document "%(partner_name)s" (Draft Invoice *%(invoice)s) in DNIT',
                    partner_name=error_invoice.partner_id.name, invoice=error_invoice.id)
            else:
                msg = _('We couldn\'t validate the invoice in DNIT.')
            msg += _('This is what we get:\n%s\n\nPlease make the required corrections and try again', str(return_info))

            # if we've already validate any invoice, we've commit and we want to inform which invoices were validated
            # which one were not and the detail of the error we get. This ins neccesary because is not usual to have a
            # raise with changes commited on databases
            if validated:
                unprocess = self - validated - error_invoice
                msg = _(
                    """Some documents where validated in DNIT but as we have an error with one document the batch validation was stopped

* These documents were validated:
%(validate_invoices)s
* These documents weren\'t validated:
%(invalide_invoices)s
""",
                    validate_invoices="\n   * ".join(validated.mapped('name')),
                    invalide_invoices="\n   * ".join([
                        _('%(item)s: "%(partner)s" amount %(amount)s', item=item.display_name, partner=item.partner_id.name, amount=item.amount_total_signed) for item in unprocess
                    ])
                )
            raise UserError(msg)

        return validated + super(AccountMove, self - py_edi_invoices)._post(soft=soft)


    def _l10n_py_do_dnit_ws_request(self):
        """ Submits the invoice information to DNIT and gets a response of DNIT in return.

        If we receive a positive response from  DNIT then validate the invoice and save the returned information in the
        corresponding invoice fields:

        * CDC number (Authorization Electronic Code)
        * Authorization Type
        * JSON Request
        * XML Request
        * JSON Response
        * Result (Approved, Aproved with Observations)

            NOTE: If there are observations we leave a message in the invoice message chart with the observation.

        If there are errors it means that the invoice has been Rejected by DNIT and we raise an user error with the
        processed info about the error and some hint about how to solve it. The invoice is not valided.
        """
        self._prepare_l10n_py_ws_data()
        return

    def __process_l10n_py_dnit_ws_request(self, all):
        response = requests.post(
            self._get_l10n_py_dnit_ws_url("recibe"),  json=json.loads(json.dumps(all)), allow_redirects=False)    
        if response.status_code == 301:
            response = requests.post( response.headers['Location'],  json=json.loads(json.dumps(all)))
        if response.status_code != 200:
            _logger.error( "Error: %s" % str(response.status_code))
            self.l10n_py_dnit_ws_response_fecproc = datetime.now()
            self.l10n_py_dnit_ws_response_estres = 'E'
            self.l10n_py_dnit_ws_response_codres = str(response.status_code)
            self.l10n_py_dnit_ws_response_msgres = response.text
            #return self._aipy_create_notification( _('Error!'), 'danger', str(response.status_code) + " " + response.text)
            return False
        else:
            return self._aipy_json_responseDNIT(response)

    def _aipy_json_responseDNIT( self, response_data):
        """
        Process the response from the DNIT
        """
        response = response_data.json()
        # {
        #   'dEstRes': E, A, O, R
        #   'dCodRes': 0 o 260 o otro numero
        #   'dMsgRes': Mensaje de error
        #   'dId': CDC
        #   'dFecProc': Fecha en modo texto
        #   'dEstResDet':  Aprobado, Aprobado con observaciones, Rechazado
        #   'dProtAut': Codigo que no se para que sirve
        # }
        self.l10n_py_dnit_ws_response_json = json.dumps(response, indent=4)
        self.l10n_py_dnit_ws_response_fecproc = datetime.now()

        response_value = libpydnitws.process_response_dnit( response)
        if response_value.get('dEstRes') == 'E':
            self.l10n_py_dnit_ws_response_estres = 'E'
            self.l10n_py_dnit_ws_response_codres = response_value.get('dCodRes')
            self.l10n_py_dnit_ws_response_msgres = response_value.get('dMsgRes')
            msg = "Error: " + str(response_value.get('dCodRes')) + " " + str(response_value.get('dMsgRes'))
            self.message_post(body=msg, message_type='notification')
            return False

        self.l10n_py_dnit_ws_response_cdc = response_value.get('dEstRes')
        self.l10n_py_dnit_ws_response_fecproc = datetime.strptime(str(response_value.get('dFecProc')), "%Y-%m-%dT%H:%M:%S")  
        self.l10n_py_dnit_ws_response_estres = response_value.get('dEstRes')
        self.l10n_py_dnit_ws_response_codres = response_value.get('dCodRes')
        self.l10n_py_dnit_ws_response_msgres = response_value.get('dMsgRes')

        if response_value.get('dEstRes') == None or response_value.get('dEstRes') == 'R':
            msg = "Warning: Documento " + str(response_value.get('dEstResDet')) + "\n[" + str(response_value.get('dCodRes')) + "-" + str(response_value.get('dMsgRes')) + "] "
            return False

        msg = "Success: Documento " + str(response_value.get('dEstResDet')) + "\n[" + str(response_value.get('dCodRes')) + "-" + str(response_value.get('dMsgRes')) + "] "
        return True


