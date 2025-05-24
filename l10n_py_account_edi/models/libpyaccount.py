#

from odoo.addons.account.models.account_move import AccountMove
from odoo import _
from odoo.exceptions import UserError

from . import libpystring

def get_tipoDocumento( moveType): #C002
    """
    Get the document type based on the move type.
    """
    value = 0
    if moveType == 'entry':            #'Journal Entry'
        value = -1
    elif moveType == 'out_invoice':    #'Customer Invoice'
        value = 1                      # Fact Elect de Expo=2, Fact Elect de Imp=3
    elif moveType == 'out_refund':     #'Customer Credit Note'
        value = 5                      # Nota de Debito=6
    elif moveType == 'in_invoice':     #'Vendor Bill'
        value = 4                      # AutoFactura
    elif moveType == 'in_refund':      #'Vendor Credit Note'
        return '05'
    elif moveType == 'out_receipt':    #'Sales Receipt'
        value = -2
    elif moveType == 'in_receipt':     #'Purchase Receipt'
        value = -3
    else:
        raise UserError(_("Document type is invalid (%s)" % moveType))
    return value

def get_factura(): #E010
    factura = {}
    # 1: Operacion presencial
    # 2: Operacion electronica
    # 3: Operacion telemarketing
    # 4: Venta a domicilio
    # 5: Operacion bancaria
    # 6: Operacion ciclica
    # 9: Otro
    factura.update({"presencia": 1}) #E011
    return factura

def _get_condicion_operacion_credito(date, date_due): #E640
    diff = date_due - date
    credito = {}
    credito.update({"tipo": 1}) #E641   Plazo  2=Cuota
    credito.update({"plazo": str(diff.days) + " días"}) #E643
    return credito

def _get_condicion_operacion_contado_entregas(monto): #E605
    entregaContado = {}
    entregaContado.update({"tipo": 1}) #E606
    entregaContado.update({"monto": monto}) 
    entregaContado.update({"moneda": "PYG"}) #E609
    entregas = []
    entregas.append(entregaContado)
    return entregas

def get_condicion_operacion( date, date_due, monto): #E600
    condicion = {}

    if date_due and date_due > date:
        condicion.update({"tipo": 2}) #E601 Credito
        condicion.update({"credito": _get_condicion_operacion_credito(date, date_due)}) #E640
    else:
        condicion.update({"tipo": 1}) #E601 Contado
        condicion.update({"entregas": _get_condicion_operacion_contado_entregas(monto)}) #605
    return condicion

def get_motivo_nce(ref):
    ncnd = {}
    if ref:
       value = libpystring.compare_strings(ref)
       ncnd.update({"motivo": value}) #E401
    else:
        ncnd.update({"motivo": '2'}) #E401
    return ncnd

def get_docuemnto_asociado( moveId:AccountMove):
    _TYPE_DOC = {
            'entry': '0',
            'out_invoice': '1',
            'out_refund': '2',
            'in_invoice': '0',
            'in_refund': '3',
            'out_receipt': '4',
            'in_receipt': '0',

    }
    documento = {}
    if moveId and moveId.l10n_py_dnit_ws_response_cdc and moveId.l10n_py_dnit_ws_response_cdc != None:
        documento.update({"formato":1}) #H002 Documento electronico
        documento.update({"cdc":moveId.l10n_py_dnit_ws_response_cdc}) #H004
    elif moveId:
        documento.update({"formato":2}) #H002 Documento impreso
        documento.update({"tipo":_TYPE_DOC[moveId.move_type]}) #H009
        documento.update({"timbrado": moveId.journal_id.l10n_py_dnit_timbrado}) #H005
        exp, pos, numbero = moveId.l10n_latam_document_number.split('-')
        documento.update({"establecimiento": exp}) #H006
        documento.update({"punto": pos}) #H007
        documento.update({"numero": numbero}) #H008
    return documento