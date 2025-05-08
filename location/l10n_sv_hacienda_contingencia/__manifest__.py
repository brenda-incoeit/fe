# -*- coding: utf-8 -*-
{
    'name': "l10n_sv Contingencia",

    'summary': """
        Proceso de gestión de contingencias y generación de DTE por lotes
        
        """,

    'description': """
        Proceso de gestión de contingencias y generación de DTE por lotes
    """,

    "author": "Daniel Jove<daniel.jove@service-it.com.ar>",
    "license": "Other proprietary",
    'website': "https://service-it.com.ar",
    'category': 'Accounting',
    "version": "16.0.1",


    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_sv',
        'account',
                
        "l10n_sv_hacienda",   # webservice de Hacienda
        "base_sv",
        "l10n_sv_haciendaws_fe",
        
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_contingencia.xml',
        'views/menuitem.xml',
        'views/account_move_views.xml',
    ],
    # only loaded in demonstration mode
    "demo": [],
    "images": [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
