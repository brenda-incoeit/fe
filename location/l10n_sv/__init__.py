# -*- coding: utf-8 -*-
from . import models

from odoo import api, SUPERUSER_ID
from odoo.exceptions import ValidationError

## Comentado por Kevin Lopez para evitar que el modulo no se instale en ambientes con registros
""" def drop_data(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    journal_ids = env['account.journal'].search([('code', 'in', ['INV', 'FACTU'])])
    moves = env['account.move'].search([('journal_id','in', journal_ids.ids)])
    if moves:
        raise ValidationError("Ya hay asientos guardados para continuar por favor eliminelos")
    for j in journal_ids:
        j.active = False
    tax_ids = env['account.tax'].search([('name', 'in', ['Tax 15.00%', 'Impuesto 15.00%'])])
    for t in tax_ids:
        t.unlink()
    partner_ids = env['res.partner'].search([('vat', '=', True)])
    for p in partner_ids:
        p.nit = p.vat
    company_ids = env['res.company'].search(['|', ('vat', '=', True), ('company_registry', '=', True)])
    for p in company_ids:
        p.nit = p.vat
        p.nrc = p.company_registry
 """