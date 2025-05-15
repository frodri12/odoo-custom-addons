# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class l10nPyAccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    l10n_py_price_unit_iva0  = fields.Float(compute='_l10n_py_compute_totals', store=True)
    l10n_py_price_unit_iva5  = fields.Float(compute='_l10n_py_compute_totals', store=True)
    l10n_py_price_unit_iva10 = fields.Float(compute='_l10n_py_compute_totals', store=True)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _l10n_py_compute_totals(self):
        #AccountTax = self.env['account.tax']
        for line in self:
            if line.display_type not in ('product', 'cogs'):
                continue
            #
            AccountTax = line.tax_ids
            #
            dTotOpeItem = line.price_unit * line.quantity
            if line.discount and line.discount > 0:
                dTotOpeItem = (line.price_unit * ( 1 - (line.discount / 100))) * line.quantity

            ivaTipo = 1
            ivaBase = AccountTax.l10n_py_tax_base
            ivaAmount = AccountTax.amount
            if ivaBase < 100 and ivaBase > 0:
                ivaTipo = 4
                ivaAmount = ivaAmount * 100 / ivaBase
            if ivaAmount == 0:
                ivaTipo = 3
                ivaAmount = 0
            #
            line.l10n_py_price_unit_iva0 = 0.0
            line.l10n_py_price_unit_iva5 = 0.0
            line.l10n_py_price_unit_iva10 = 0.0

            #
            if ivaTipo == 3:
                line.l10n_py_price_unit_iva0 = dTotOpeItem
            elif ivaTipo == 1 and ivaAmount == 5:
                line.l10n_py_price_unit_iva5 = dTotOpeItem
            elif ivaTipo == 1 and ivaAmount == 10:
                line.l10n_py_price_unit_iva10 = dTotOpeItem
            elif ivaTipo == 4:
                line.l10n_py_price_unit_iva0 = (100 * dTotOpeItem * (100 - ivaBase)) / (10000 + (ivaAmount * ivaBase))
                if ivaAmount == 5:
                    line.l10n_py_price_unit_iva5 = (100 * dTotOpeItem * ivaBase) / (10000 + (ivaAmount * ivaBase))
                if ivaAmount == 10:
                    line.l10n_py_price_unit_iva10 = (100 * dTotOpeItem * ivaBase) / (10000 + (ivaAmount * ivaBase))



    def _get_l10n_py_dnit_ws_item(self):
        productId = self.product_id
        uomId = productId.uom_id
        item = {}
        item.update({"codigo": productId.default_code if productId.default_code else productId.id}) #E701
        item.update({"descripcion": productId.name}) #E708
        if uomId.l10n_py_dnit_code:
            item.update({"unidadMedida": uomId.l10n_py_dnit_code}) #E709
        item.update({"cantidad": self.quantity}) #E711
        # E8 E704-E707 - Pendiente de implementar
        item.update({"pais": "PRY"}) #E712
        item.update({"observacion": productId.name}) #E714
        # E8 E715-E719 - Pendiente de implementar
        item.update({"precioUnitario": self.price_unit}) #E721
        if self.currency_id.name != 'PYG':
            item.update({"cambio": 1 / self.currency_rate}) #E725
        # E8.1.1 EA001-EA007 - Pendiente de implementar
        ivaTipo = 1
        ivaBase = self.tax_ids.l10n_py_tax_base
        ivaAmount = self.tax_ids.amount
        if ivaAmount == 0:
            ivaTipo = 3
        elif ivaBase < 100 and ivaBase > 0:
            ivaAmount = self.tax_ids.amount * 100 / ivaBase
            ivaTipo = 4
        item.update({"ivaTipo": ivaTipo}) #E731
        item.update({"ivaBase": 0 if ivaTipo == 3 else ivaBase}) #E733
        item.update({"iva": ivaAmount}) #E734
        # E8.4 E750-E760 - Pendiente de implementar
        # E8.5 E770-E789 - Pendiente de implementar
        return item