# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from random import randint
from datetime import datetime

import logging
import pytz
import json

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
        if self.l10n_latam_document_type_id.code == 'FA' and tipoTransaccion != 0:
            self._setD("tipoTransaccion", tipoTransaccion) #D011
        return items

    def _compute_economic_activity( self):
        ecos = []
        for rec in self.company_id.l10n_aipy_economic_activity_ids:
            eco = {}
            eco.update({"codigo": rec.code})
            eco.update({"descripcion": rec.name})
            ecos.append(eco)
        return ecos
                
    def _compute_estabecimientos( self):
        estabecimientos = []
        est = {}
        est.update({"codigo": self.company_id.l10n_aipy_dnit_organization})
        est.update({"direccion": self.company_id.street}) #D107
        est.update(
            {"numeroCasa": self.company_id.l10n_aipy_house if self.company_id.l10n_aipy_house else 0}) #D108
        if self.company_id.street2:
            est.update({"complementoDireccion1": self.company_id.street2}) #D109
        est.update({"departamento": self.company_id.state_id.code}) #D111
        est.update({"ciudad": self.company_id.l10n_aipy_city_id.code}) #D115
        est.update({"distrito": self.company_id.l10n_aipy_district_id.code}) #D113
        est.update({"telefono": self.company_id.phone}) #D117
        est.update({"email": self.company_id.email}) #D118
        estabecimientos.append(est)
        return estabecimientos
                
    def _compute_regimeType( self):
        if self.company_id.l10n_aipy_regime_type_id:
            value = self.company_id.l10n_aipy_regime_type_id.code
            if value > 0:
                self._setP("tipoRegimen", value)
                
    #############################


    def dnit_generate_json( self):
        """
        Generate the JSON file for the DNIT
        """
        # Initialize data
        self._initialize_data()
        # Set Params
        self._setP("ruc", self.company_id.vat) #D102
        self._setP("tipoContribuyente", 1 if self.company_id.partner_id.company_type == 'person' else 2) #D103
        self._setP("razonSocial", self.company_id.name) #D105
        if self.company_id.l10n_aipy_fantasy_name:
            self._setP("nombreFantasia", self.company_id.l10n_aipy_fantasy_name) #D106
        if self.company_id.l10n_aipy_testing_mode:
            self._setP("nombreFantasia", self.company_id.name)
            self._setP("razonSocial", "DE generado en ambiente de prueba - sin valor comercial ni fiscal") #D105
        self._compute_regimeType()

        self._setP("actividadesEconomicas", self._compute_economic_activity())
        self._setP("establecimientos", self._compute_estabecimientos())

        # Set Data
        self._setD("items", self._compute_statement_lines())
        #
        _logger.info( "----- JSON PARAMS ----")
        _logger.warning( "\n -- PARAMS -- \n" + json.dumps(_params, indent=4) + "\n")
        _logger.info( "----- JSON DATA ----")
        _logger.warning( "\n -- DATA -- \n" + json.dumps(_data, indent=4) + "\n")
