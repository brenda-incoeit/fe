# -*- coding: utf-8 -*-
{
    'name': "l10n_sv_hacienda_invalidadion",

    'summary': """
        Proceso de invalidadion
        m""",

    'description': """
        Proceso de invalidadion
    """,

    "author": "Daniel Jove<daniel.jove@service-it.com.ar>",
    "license": "Other proprietary",
    'website': "https://service-it.com.ar",

    'category': 'Accounting',
    "version": "17.0.1",

    # any module necessary for this one to work correctly
    'depends': ['base',
        "l10n_sv_hacienda",   # webservice de Hacienda
        "base_sv",
        # "l10n_invoice_sv",
        # "account_debit_note",
        "l10n_sv_haciendaws_fe",                ],

    # always loaded
    'data': [
        "views/account_move_views.xml",
        "security/ir.model.access.csv",
    ],
    # only loaded in demonstration mode
    "demo": [],
    "images": [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
