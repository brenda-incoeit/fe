# -*- coding: utf-8 -*-
from odoo import fields, models, api


class sit_account_move_line(models.Model):
    
    _inherit = 'account.move.line'
    tax_hacienda = fields.Many2one('account.move.tributos.field')
