# -*- coding: utf-8 -*-
{
    'name': "Paraguayan Electronic Invoicing",
    'website': "https://www.avatar.com.py",
    'icon': '/account/static/description/l10n.png',
    'countries': ['py'],
    'version': '0.1',
    'author': "Avatar Informatica SRL",
    'category': 'Accounting/Localizations/EDI',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_aipy'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        
        'views/account_move_view.xml',
        'views/res_partner_view.xml',

        #'static/src/core/notifications/notification.xml',
        
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': ['l10n_aipy'],
    'license': 'LGPL-3',
    'assets': {
        'web._assets_core': [
            ('replace', 'web/static/src/core/notifications/notification.xml', 'l10n_aipy_edi/static/src/core/notifications/notification.xml'),
            ('replace', 'web/static/src/core/notifications/notification.scss', 'l10n_aipy_edi/static/src/core/notifications/notification.scss'),
            ('replace', 'web/static/src/core/notifications/notification.variables.scss', 'l10n_aipy_edi/static/src/core/notifications/notification.variables.scss'),
        ],
    }
}

