# -*- coding: utf-8 -*-
{
    'name': "Paraguay - Accounting",
    'website': "https://www.avatar.com.py",
    'icon': '/account/static/description/l10n.png',
    'countries': ['py'],
    'version': '0.3',
    'author': "Avatar Informatica SRL",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
############    'category': 'Accounting/Localizations/Account Charts',
    'description': """
General Chart of Accounts.
==========================

This module adds accounting functionalities for the Paraguayan localization, representing the minimum required configuration for a company to operate in Paraguay under the regulations and guidelines provided by the DNIT (Dirección Nacional de Ingresos Tributarios).

Among the functionalities are:

* Paraguayan Generic Chart of Account
* Pre-configured VAT Taxes and Tax Groups.
* Legal document types in Paraguay.
* Valid contact identification types in Paraguay.
* Configuration and activation of Paraguayan Currencies  (PYG).
* Frequently used default contacts already configured: DNIT, Consumidor Final Paraguayo.

Configuration
-------------

Demo data for testing:

* Paraguayan company named "PY Company" with the Paraguayan chart of accounts already installed, pre configured taxes, document types and identification types.
* Paraguayan contacts for testing:

   * IEB Internacional
   * Consumidor Final Anónimo Uruguayo.

       """,
    # any module necessary for this one to work correctly
    'depends': [
        'account',
        'l10n_latam_invoice_document',
        'l10n_latam_base',
    ],
    #'auto_install': ['account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/res_country_state_data.xml',
        'data/uom_uom_data.xml',
        'data/res.country.csv',
        'data/l10n_aipy_district_data.xml',
        'data/l10n_aipy_city_data.xml',
        'data/l10n_aipy_city_data02.xml',
        'data/l10n_aipy_city_data03.xml',
        'data/res_currency_data.xml',
        'data/res_users_data.xml',
        'data/res_partner_data.xml',
        'data/l10n_latam_identification_type_data.xml',
        'data/l10n_latam_document_type_data.xml',
        'data/l10n_aipy_regime_type_data.xml',

        'views/uom_uom_view.xml',
        'views/res_partner_view.xml',
        'views/res_country_view.xml',
        'views/res_company_view.xml',
        'views/account_journal_view.xml',
        'views/account_tax_view.xml',
        'views/account_move_view.xml',
        'views/l10n_aipy_economic_activity_view.xml',
        'views/report_invoice.xml',
        
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo_company.xml',
    ],
    'license': 'LGPL-3',
    'pre_init_hook': '_set_change_values',
    'external_dependencies': {
        'python': ['tzdata']
    },
}

