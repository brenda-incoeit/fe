##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Coloco las funciones de WS aqui para limpiar el codigo
# de funciones que no ayudan a su lectura

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('invoice_payment_term_id')
    def _onchange_(self):
        for record in self:
            con_pag = record.invoice_payment_term_id.condiciones_pago
            if con_pag:
                if con_pag == "1":
                    record.condiciones_pago = con_pag
                    record.sit_plazo =  False
                    record.sit_periodo = False
                if con_pag == "2":
                    record.condiciones_pago = con_pag
                    record.sit_plazo = record.invoice_payment_term_id.sit_plazo or False
                    record.sit_periodo = record.invoice_payment_term_id.sit_periodo or False

class AccountMoveReversal(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _inherit = 'account.move.reversal'

    @api.depends('move_ids')
    def _compute_journal_id(self):
        for record in self:
            j_id = self.env['account.journal'].search([('code','=','NDC')])
            if record.journal_id:
                record.journal_id = record.journal_id
            else:
                journals = record.move_ids.journal_id.filtered(lambda x: x.active)
                record.journal_id = journals[0] if journals else None
            if j_id:
                record.journal_id = j_id