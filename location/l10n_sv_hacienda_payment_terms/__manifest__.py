# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Añade configuracion para terminos de pagos hacienda sv",
    "version": "17.1",
    "author": "Gerardo-MiRe",
    "category": "Point of Sale",
    'website': 'https://github.com/Gerardo-MiRe',
    "depends": [
        "l10n_sv_haciendaws_fe",
        "l10n_sv",
        "base",
    ],
    "data": [
        'views/account_payment_term.xml',
        'views/account_move.xml'
    ],
    "installable": True,
    "auto_install": False,
}
