# -*- coding: utf-8 -*-
{
    'name': "l10n_sv Factura de Exportacion",
    'summary': """
        Factura de Exportacion
        """,
    'description': """
        Factura de Exportacion
    """,
    "author": "Naun Flores<naunflores620@gmail.com>",
    "license": "Other proprietary",
    'website': "https://prosolutions.com.sv",
    'category': 'Accounting',
    "version": "16.0.1",
    'depends': ['base',
        "l10n_sv_hacienda",   # webservice de Hacienda
        "base_sv",
        # "l10n_invoice_sv",
        # "account_debit_note",
        "l10n_sv_haciendaws_fe",                ],
    # always loaded
    'data': [
    #     "views/account_move_views.xml",
    ],
    "demo": [],
    "images": [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
