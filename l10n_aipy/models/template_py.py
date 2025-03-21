# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.addons.account.models.chart_template import template

class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('py')
    def _get_py_template_data(self):
        return {
            'property_account_receivable_id': 'base_deudores_por_ventas', # 1.1.3.01.010 Creditos por ventas
            'property_account_payable_id': 'base_proveedores', # 2.1.1.01.010 Proveedores
            'property_account_income_categ_id': 'base_venta_de_mercaderia', # 4.1.1.01.010 Venta de mercaderia
            'property_account_expense_categ_id': 'base_cmv', # 5.1.1.01.010 Costo de mercaderia vendida
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
                #'deferred_expense_account_id': 'uy_code_11407',
                #'deferred_revenue_account_id': 'uy_code_21321',
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
                "code": "002",
                "l10n_latam_use_documents": True,
                "refund_sequence": True,
                "debit_sequence": True,
            },
        }

    def _load(self, template_code, company, install_demo):
        res = super()._load(template_code, company, install_demo)
        if template_code == 'py':
            company.partner_id.l10n_latam_identification_type_id = self.env.ref('l10n_aipy.it_ruc')
        return res
