#

from odoo.exceptions import ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


from . import libpydate
import json
import re

# response_data = libdnitws.get_response_dnit( response_data)
# self.l10n_py_dnit_ws_response_json = json.dumps(response_data.json(), indent=4)
# self.l10n_py_dnit_ws_response_fecproc = datetime.now()
# self.l10n_py_dnit_ws_response_estres = 'E'
# self.l10n_py_dnit_ws_response_msgres = response.get("message")
# self.l10n_py_dnit_ws_response_cdc = dId
# self.l10n_py_dnit_ws_response_fecproc = datetime.strptime(dFecProc, "%Y-%m-%dT%H:%M:%S")
# self.l10n_py_dnit_ws_response_estres = dEstRes[:1]
# self.l10n_py_dnit_ws_response_codres = dCodRes
# self.l10n_py_dnit_ws_response_msgres = dMsgRes


def process_response_dnit( response_data):
    """
    Process the response from the DNIT
    """
    return_value = {}
    #response = response_data.json()
    response = json.loads(response_data) 

    if int(response['code']) != 0:
        _logger.error("Response = \n" + json.dumps(response, indent=2))     
        return_value.update({'dEstRes': 'E'})
        return_value.update({'dCodRes': str(response['code'])})
        return_value.update({'dMsgRes': response.get("message")})
        payload = response.get("payload")
        if payload and payload != None:
            if payload.get('errno') and payload.get('errno') != None:
                return_value.update({'dCodRes': str(payload['errno'])})
            if payload.get('errstr') and payload.get('errstr') != None:
                return_value.update({'dMsgRes': str(payload['errstr'])})
        return return_value

    _logger.info("Response = \n" + json.dumps(response, indent=2)) 
    rProtDe = _get_rProtDe( response)
    rResEnviLoteDe = _get_rResEnviLoteDe( response)
    if rProtDe == None and rResEnviLoteDe == None:
        return return_value
    if rProtDe != None:
        return_value.update({'dId': rProtDe.get("ns2:Id")})
        #return_value.update({'dFecProc': libpydate.from_date2utc(rProtDe.get("ns2:dFecProc"))})
        #return_value.update({'dFecProc': datetime.strptime((rProtDe.get("ns2:dFecProc")[0:10] + " " + rProtDe.get("ns2:dFecProc")[11:19]), "%Y-%m-%d %H:%M:%S")})
        return_value.update({'dFecProc': rProtDe.get("ns2:dFecProc")[0:19]})
        if rProtDe.get("ns2:dEstRes") == None:
            return_value.update({'dEstRes': "E"})
        else:
            return_value.update({'dEstRes': rProtDe.get("ns2:dEstRes")[:1]})
        return_value.update({'dEstResDet': rProtDe.get("ns2:dEstRes")})
        return_value.update({'dProtAut': rProtDe.get("ns2:dProtAut")})

        gResProc = rProtDe.get("ns2:gResProc")
        if not gResProc or gResProc == None:
            return return_value

        if str(type(gResProc)) == "<class 'dict'>":
            return_value.update({'dCodRes': gResProc.get("ns2:dCodRes")})
            return_value.update({'dMsgRes': gResProc.get("ns2:dMsgRes")})
        elif str(type(gResProc)) == "<class 'list'>":
            for rec in gResProc:
                return_value.update({'dCodRes': rec.get("ns2:dCodRes")})
                return_value.update({'dMsgRes': rec.get("ns2:dMsgRes")})
    
    if rResEnviLoteDe != None:
        return_value.update({'dFecProc': rResEnviLoteDe.get("ns2:dFecProc")[0:19]})
        return_value.update({'dCodRes': rResEnviLoteDe.get("ns2:dCodRes")})
        return_value.update({'dMsgRes': rResEnviLoteDe.get("ns2:dMsgRes")})
        return_value.update({'dProtConsLote': rResEnviLoteDe.get("ns2:dProtConsLote")})
        return_value.update({'dTpoProces': rResEnviLoteDe.get("ns2:dTpoProces")})
        return_value.update({'dEstRes': 'L'})
        return_value.update({'dEstResDet': 'Lote'})

    return return_value

def _get_rProtDe( response):
    payload = response.get("payload")
    if not payload or payload == None:
        return None
    rRetEnviDe = payload.get("ns2:rRetEnviDe")
    if not rRetEnviDe or rRetEnviDe == None:
        return None
    return rRetEnviDe.get("ns2:rProtDe")

def _get_rResEnviLoteDe( response):
    payload = response.get("payload")
    if not payload or payload == None:
        return None
    rResEnviLoteDe = payload.get("ns2:rResEnviLoteDe")
    if not rResEnviLoteDe or rResEnviLoteDe == None:
        return None
    return rResEnviLoteDe

#####################

def format_response( response_data):
    response = json.loads(response_data)
    res = {}
    #
    code = response.get('code')
    if not code or code == None:
        # Error insesperado
        _logger.error("Response = \n" + json.dumps(response, indent=2)) 
        return res

    if int(code) != 0:
        # Error en WS
        _logger.error("Response = \n" + json.dumps(response, indent=2)) 
        res.update({'dEstRes': 'E'})
        res.update({'dCodRes': str(code)})
        res.update({'dMsgRes': response.get('message')})
        payload = response.get("payload")
        if payload and payload != None:
            errno = payload.get('errno')
            errstr = payload.get('errstr')
            if errno and errno != None:
                res.update({'dCodRes': errno})
            if errstr and errstr != None:
                res.update({'dMsgRes': errstr})
        return res

    #
    _logger.info("Response = \n" + json.dumps(response, indent=2)) 
    rProtDe = response.get('ns2:rProtDe')
    if rProtDe and rProtDe != None:
        # WS recepción documento electrónico – siRecepDE
        res.update({ 'cdc': rProtDe.get('ns2:id') })
        res.update({ 'dFecProc': rProtDe.get('ns2:dFecProc') })
        res.update({ 'dDigVal': rProtDe.get('ns2:dDigVal') })
        res.update({ 'dEstRes': rProtDe.get('ns2:dEstRes') })
        res.update({ 'dProtAut': rProtDe.get('ns2:dProtAut') })
        gResProc = rProtDe.get('ns2:gResProc')
        if gResProc and gResProc != None:
            res.update({ 'dCodRes': gResProc.get('ns2:dCodRes') })
            res.update({ 'dMsgRes': gResProc.get('ns2:dMsgRes') })
        return res
    #
    rResEnviLoteDe = response.get('ns2:rResEnviLoteDe')
    if rResEnviLoteDe and rResEnviLoteDe != None:
        # WS recepción lote DE – siRecepLoteDE
        res.update({ 'dFecProc': rResEnviLoteDe.get('ns2:dFecProc') })
        res.update({ 'dCodRes': rResEnviLoteDe.get('ns2:dCodRes') })
        res.update({ 'dMsgRes': rResEnviLoteDe.get('ns2:dMsgRes') })
        res.update({ 'dProtConsLote': rResEnviLoteDe.get('ns2:dProtConsLote') })
        res.update({ 'dTpoProces': rResEnviLoteDe.get('ns2:dTpoProces') })
        return res
    #
    rResEnviConsLoteDe = response.get('ns2:rResEnviConsLoteDe')
    if rResEnviConsLoteDe and rResEnviConsLoteDe != None:
        # WS consulta resultado de lote DE – siResultLoteDE
        res.update({ 'dFecProc': rResEnviConsLoteDe.get('ns2:dFecProc') })
        res.update({ 'dCodResLot': rResEnviConsLoteDe.get('ns2:dCodResLot')})
        res.update({ 'dMsgResLot': rResEnviConsLoteDe.get('ns2:dMsgResLot')})
        gResProcLote = rResEnviConsLoteDe.get('ns2:gResProcLote')
        if gResProcLote and gResProcLote != None:
            res.update({ 'cdc': gResProcLote.get('ns2:id') })
            res.update({ 'dEstRes': gResProcLote.get('ns2:dEstRes')})
            res.update({ 'dProtAut': gResProcLote.get('ns2:dProtAut')})
        return res


