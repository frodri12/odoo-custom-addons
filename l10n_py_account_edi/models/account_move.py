# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

_params = {}
_data = {}
_random_code = "0000000000"

class AccountMove(models.Model):

    _inherit = "account.move"

    l10n_py_dnit_cdc = fields.Char('Authorization Code', copy=False, size=44, help="Paraguay: authorization code given by DNIT after electronic invoice is created and valid.")

    l10n_py_dnit_ws_response_cdc = fields.Char(string="CDC")
    l10n_py_dnit_ws_response_fecproc = fields.Char(string="Fecha de procesado")
    l10n_py_dnit_ws_response_digval = fields.Char(string="Digito de verificacion")
    l10n_py_dnit_ws_response_estres = fields.Char(string="Estado") ## A: Aprobado, O: Aprobado con Observacion, R: Rechazado, E: Error, P; Pendiente
    l10n_py_dnit_ws_response_protaut  = fields.Char(string="Protocolo de autorizacion")
    l10n_py_dnit_ws_response_codres = fields.Char(string="Codigo de respuesta")
    l10n_py_dnit_ws_response_msgres = fields.Char(string="Mensaje de respuesta")

    l10n_py_dnit_ws_request_json = fields.Text(string="JSON de envio")
    l10n_py_dnit_ws_request_xml = fields.Text(string="XML de envio")
    l10n_py_dnit_ws_response_json = fields.Text(string="JSON de respuesta")

    # Prepare Request Data for webservices. Generate the JSON file for the DNIT
    def _l10n_py_prepare_ws_data( self):
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

        #_data.update({ key : value })

        
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
        return

"""
    def _l10n_ar_do_afip_ws_request_cae(self, client, auth, transport):
        for inv in self.filtered(lambda x: x.journal_id.l10n_py_dnit_pos_system in ('RLI_RLM','AURLI_RLM','BFERCEL','FEERCEL','CPERCEL')and x.l10n_py_dnit_ws_response_estres not in ('A','O')):
            #afip_ws = inv.journal_id.l10n_ar_afip_ws
            errors = obs = events = ''
            request_data = False
            return_codes = []
            values = {}

            #self.l10n_ar_check_rate()

            # We need to call a different method for every webservice type and assemble the returned errors if they exist
            if afip_ws == 'wsfex':
                ws_method = 'FEXAuthorize'
                last_id = client.service.FEXGetLast_ID(auth).FEXResultGet.Id
                request_data = inv.wsfex_get_cae_request(last_id+1, client)
                self._ws_verify_request_data(client, auth, ws_method, request_data)
                response = client.service[ws_method](auth, request_data)
                result = response.FEXResultAuth
                if response.FEXErr.ErrCode != 0 or response.FEXErr.ErrMsg != 'OK':
                    errors = '\n* Code %s: %s' % (response.FEXErr.ErrCode, response.FEXErr.ErrMsg)
                    return_codes += [str(response.FEXErr.ErrCode)]
                if response.FEXEvents.EventCode != 0 or response.FEXEvents.EventMsg != 'Ok':
                    events = '\n* Code %s: %s' % (response.FEXEvents.EventCode, response.FEXEvents.EventMsg)
                    return_codes += [str(response.FEXEvents.EventCode)]

                if result:
                    if result.Motivos_Obs:
                        obs = '\n* Code ???: %s' % result.Motivos_Obs
                        return_codes += [result.Motivos_Obs]
                    if result.Reproceso == 'S':
                        return_codes += ['reprocess']
                    if result.Resultado != 'A':
                        if not errors:
                            return_codes += ['rejected']
                    else:
                        values = {'l10n_ar_afip_auth_mode': 'CAE',
                                  'l10n_ar_afip_auth_code': result.Cae,
                                  'l10n_ar_afip_auth_code_due': datetime.strptime(result.Fch_venc_Cae, '%Y%m%d').date(),
                                  'l10n_ar_afip_result': result.Resultado}

            return_info = inv._prepare_return_msg(afip_ws, errors, obs, events, return_codes)
            afip_result = values.get('l10n_ar_afip_result')
            xml_response, xml_request = transport.xml_response, transport.xml_request
            if afip_result not in ['A', 'O']:
                if not self.env.context.get('l10n_ar_invoice_skip_commit'):
                    self.env.cr.rollback()
                if inv.exists():
                    # Only save the xml_request/xml_response fields if the invoice exists.
                    # It is possible that the invoice will rollback as well e.g. when it is automatically created:
                    #   * creating credit note with full reconcile option
                    #   * creating/validating an invoice from subscription/sales
                    inv.sudo().write({'l10n_ar_afip_xml_request': xml_request, 'l10n_ar_afip_xml_response': xml_response})
                if not self.env.context.get('l10n_ar_invoice_skip_commit'):
                    self.env.cr.commit()
                return return_info
            values.update(l10n_ar_afip_xml_request=xml_request, l10n_ar_afip_xml_response=xml_response)
            inv.sudo().write(values)
            if return_info:
                inv.message_post(body=Markup('<p><b>%s%s</b></p>') % (_('AFIP Messages'), plaintext2html(return_info, 'em')))
       
"""       

