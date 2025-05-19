# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(string='Number', required=True, readonly=False, copy=False, default='/')

    def _get_sequence(self):
        self.ensure_one()
        journal = self.journal_id
        if self.move_type in ('entry', 'out_invoice', 'in_invoice', 'out_receipt',
                              'in_receipt') or not journal.refund_sequence:
            return journal.sequence_id
            # si es nota de crédito y existe refund_sequence_id, lo uso
        if journal.refund_sequence_id:
            return journal.refund_sequence_id
        return

    @api.model
    def _get_standard_sequence(self):
        """Devuelve la secuencia normal (no-DTE) para el diario."""
        self.ensure_one()
        journal = self.journal_id
        # Para facturas normales o si no hay refund_sequence, uso la secuencia principal
        if self.move_type in ('entry', 'out_invoice', 'in_invoice', 'out_receipt', 'in_receipt') \
                or not journal.refund_sequence:
            return journal.sequence_id
        # Para notas de crédito, uso refund_sequence_id si existe
        return journal.refund_sequence_id

    def _post(self, soft=True):
        # 1) Solo asigno la secuencia estándar para diarios NO sale
        non_sales = self.filtered(lambda m: m.journal_id.type != 'sale')
        for move in non_sales:
            if move.name == '/':
                journal = move.journal_id
                if not journal:
                    raise UserError(_('Debe seleccionar un Diario antes de confirmar el documento.'))
                sequence = move._get_standard_sequence()
                if not sequence:
                    raise UserError(
                        _('Por favor defina una secuencia para el Diario "%s".') %
                        journal.display_name
                    )
                # Asigno el siguiente número de la secuencia normal
                move.name = sequence.with_context(
                    ir_sequence_date=move.date
                ).next_by_id()

        # 2) Delego al super(), de modo que:
        #    - los diarios sale pasen a tu flujo DTE (con “DTE-…”)
        #    - todo lo demás continúe con la lógica de Odoo
        return super(AccountMove, self)._post(soft=soft)

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.name = '/'
        self._compute_name()

    def _constrains_date_sequence(self):
        return

    def write(self, vals):
        # para evitar que pongan name = False
        if 'name' in vals and vals['name'] is False:
            vals['name'] = '/'
        return super().write(vals)