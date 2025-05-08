# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.addons.account.models.chart_template import template

class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('py')
    def _get_py_template_data(self):
        return {
            'property_account_receivable_id': 'base_deudores_por_ventas', 
            'property_account_payable_id': 'base_proveedores', 
            'property_account_income_categ_id': 'base_venta_de_mercaderia', 
            'property_account_expense_categ_id': 'base_compra_mercaderia', 
            'code_digits': '12',
            'name': _('Paraguayan Generic Chart of Accounts'),
        }

    @template('py', 'res.company')
    def _get_py_res_company(self):
        return {
            self.env.company.id: {
                'account_fiscal_country_id': 'base.py',
                'bank_account_code_prefix': '1.1.1.02.',
                'cash_account_code_prefix': '1.1.1.01.',
                'transfer_account_code_prefix': '6.0.00.00.',
                'account_default_pos_receivable_account_id': 'base_deudores_por_ventas_pos',
                'income_currency_exchange_account_id': 'base_diferencias_de_cambio',
                'expense_currency_exchange_account_id': 'base_diferencias_de_cambio',
                'account_journal_early_pay_discount_loss_account_id': 'base_diferencias_de_cambio',
                'account_journal_early_pay_discount_gain_account_id': 'base_diferencias_de_cambio',
                'account_sale_tax_id': 'vat2',
                'account_purchase_tax_id': 'vat5',
                'deferred_expense_account_id': 'base_cheques_de_terceros_rechazados',
                'deferred_revenue_account_id': 'base_cheques_diferidos',
            },
        }

    @template('py', 'account.journal')
    def _get_py_account_journal(self):
        return {
            'sale': {
                "name": _("Customer Invoices"),
                "code": "001",
                "l10n_latam_use_documents": True,
                "refund_sequence": True,
                "debit_sequence": True,
            },
            'purchase': {
                "name": _("Vendor Bills"),
                "code": "VB01",
                "l10n_latam_use_documents": True,
                "refund_sequence": True,
                "debit_sequence": True,
            },
        }

    def _load(self, template_code, company, install_demo, force_create=True):
        res = super()._load(template_code, company, install_demo, force_create)
        if template_code == 'py':
            company.partner_id.l10n_latam_identification_type_id = self.env.ref('l10n_aipy.it_ruc')
        return res
