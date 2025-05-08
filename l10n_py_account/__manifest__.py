# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Paraguay - Accounting",
    'website': "https://www.avatar.com.py",
    'icon': '/account/static/description/l10n.png',
    'countries': ['py'],
    'version': '0.4',
    'author': "Avatar Informatica SRL",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations/Account Charts',
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
    # always loaded
    'data': [
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'license': 'LGPL-3',
}
