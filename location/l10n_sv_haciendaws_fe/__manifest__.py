{
    "name": "Factura Electrónica El Salvador",
    "version": "16.0.1",
    "category": "Localization/ElSalvador",
    "sequence": 14,
    "author": "Daniel Jove <daniel.jove@service-it.com.ar>",
    "license": "Other proprietary",
    "summary": "",
    "depends": [ 
        "l10n_sv_hacienda",   # webservice de Hacienda
        "base_sv",
        "l10n_invoice_sv",
        "account_debit_note",
        "l10n_latam_invoice_document"
    ],
    "external_dependencies": {},
    "data": [
        "views/account_move_views.xml",
        "views/account_journal_view.xml",
        # "data/account.journal.csv",
        "views/ir_cron.xml",
        "wizard/account_validate_account_move.xml",
        'views/view_account_move_hacienda_tab.xml',
        "data/l10n_latam.document.type.csv",
        "views/account_move_reversal_view.xml",
        "views/account_move_nc_view.xml"
    ],
    "demo": [],
    "images": [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
