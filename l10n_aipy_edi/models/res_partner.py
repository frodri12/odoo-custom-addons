# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import ValidationError, UserError

import logging
import requests
import json
from markupsafe import Markup



_logger = logging.getLogger(__name__)

class ResPartner(models.Model):

    _inherit = 'res.partner'

    def _create_notification( self, title, type, body):
        message = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'type': type,
                'message': body,
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
        return message

    def _get_url( self, key):
        sKey = 'aipy_edi.url.' + str(key)
        if self.env.company.l10n_aipy_testing_mode:
            sKey += '.test'
        else:
            sKey += '.prod'
        ICP = self.env['ir.config_parameter'].sudo()
        sRet = str(ICP.get_param(sKey))
        return sRet

    def _decode_result( self, result):

        if result.get("code") != 0:
            self.message_post( body="check_ruc_with_DNIT=>Warning: " + str(result.get("code")) + "-" + result.get("message"), message_type='notification')
            return self._create_notification( "Warning", "warning", str(result.get("code"))  + "-" + result.get("message"))
        
        payload = result.get("payload")
        rResEnviConsRUC = None
        if payload and payload != None:
            rResEnviConsRUC = payload.get("ns2:rResEnviConsRUC")
        else:
            self.message_post( body="check_ruc_with_DNIT=>Warning: " + result.get("code") + "-" + result.get("message"), message_type='notification')
            return self._create_notification( "check_ruc_with_DNIT", "warning", result.get("code") + "-" + result.get("message"))

        xContRUC = None
        dCodRes = None
        dMsgRes = None
        if rResEnviConsRUC and rResEnviConsRUC != None:
            dCodRes = rResEnviConsRUC.get("ns2:dCodRes")
            dMsgRes = rResEnviConsRUC.get("ns2:dMsgRes")
            if dCodRes == '0502':
                xContRUC = rResEnviConsRUC.get("ns2:xContRUC")
            else:
                self.message_post( body="check_ruc_with_DNIT=>Warning: " + dCodRes + "-" + dMsgRes, message_type='notification')
                return self._create_notification( "check_ruc_with_DNIT", "warning", dCodRes + "-" + dMsgRes)

        if xContRUC and xContRUC != None:
            dRUCCons = xContRUC.get("ns2:dRUCCons")
            dRazCons = xContRUC.get("ns2:dRazCons")
            dCodEstCons = xContRUC.get("ns2:dCodEstCons")
            dDesEstCons = xContRUC.get("ns2:dDesEstCons")
            msg = str(dCodRes) + "-" + str(dMsgRes) + "\n"
            msg += "Razon Social: " + str(dRazCons) + "\n"
            msg += "Estado: " + str(dDesEstCons) + "\n"
            self.message_post( body="check_ruc_with_DNIT=>" + dRazCons, message_type='notification')
            return self._create_notification( "check_ruc_with_DNIT", "success", msg) 
        else:
            return self._create_notification( "check_ruc_with_DNIT", "info", rResEnviConsRUC.get("ns2:dCodRes") + "-" + rResEnviConsRUC.get("ns2:dMsgRes"))  
        
    def _get_data_dnit( self, data):
        response = requests.post(
            self._get_url("consulta_ruc"),  json=json.loads(json.dumps(data)), allow_redirects=False) 
        if response.status_code == 301:
            response = requests.post( response.headers['Location'],  json=json.loads(json.dumps(data)))
        if response.status_code != 200:
            self.message_post( body="check_ruc_with_DNIT=>Error: %s" % str(response.status_code))
            return self._create_notification( "check_ruc_with_DNIT", "danger", "Error: %s" % str(response.status_code)) 
        else:
            result = response.json()
            return self._decode_result( result)

    def check_ruc_with_DNIT(self):
        if self.vat:
            ruc = self.vat.split("-")[0]
            if len(ruc) > 8 or len(ruc) < 5 or not ruc.isdigit():
                raise ValidationError(_("Invalid RUC format. Expected format: XXXXXXXX-X"))
            data = {}
            data['empresa'] = self.env.company.vat.split("-")[0]
            data['produccion'] = False if self.company_id.l10n_aipy_testing_mode else True
            data['ruc'] = ruc
            data['servicio'] = "ruc"
            return self._get_data_dnit( data)

