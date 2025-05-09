# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # --- Campos existentes de secuencia ---
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Entry Sequence',
        help="This field contains the information related to the numbering of the journal entries of this journal."
    )
    sequence_number_next = fields.Integer(
        string='Next Number',
        help='The next sequence number will be used for the next invoice.',
        compute='_compute_seq_number_next',
        inverse='_inverse_seq_number_next'
    )
    refund_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Credit Note Entry Sequence',
        help="This field contains the information related to the numbering of the credit note entries of this journal."
    )
    refund_sequence_number_next = fields.Integer(
        string='Credit Notes Next Number',
        help='The next sequence number will be used for the next credit note.',
        compute='_compute_refund_seq_number_next',
        inverse='_inverse_refund_seq_number_next'
    )

    # --- Nuevo campo para prefijo DTE editable desde interfaz ---
    dte_prefix = fields.Char(
        string="Prefijo DTE",
        default="DTE",
        help="Prefijo usado al generar el número de control del DTE."
    )


    @api.model
    def _create_sequence(self, vals, refund=False):
        prefix = self._get_sequence_prefix(vals['code'], refund)
        seq_name = refund and vals['code'] + _(': Refund') or vals['code']
        seq_vals = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        if 'company_id' in vals:
            seq_vals['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq_vals)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = (
            refund and vals.get('refund_sequence_number_next', 1)
            or vals.get('sequence_number_next', 1)
        )
        return seq

    def create_sequence(self, refund):
        prefix = self._get_sequence_prefix(self.code, refund)
        seq_name = refund and self.code + _(': Refund') or self.code
        seq_vals = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        if self.company_id:
            seq_vals['company_id'] = self.company_id.id
        seq = self.env['ir.sequence'].create(seq_vals)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = (
            refund and (self.refund_sequence_number_next or 1)
            or (self.sequence_number_next or 1)
        )
        return seq

    def create_journal_sequence(self):
        if not self.sequence_id:
            seq = self.create_sequence(refund=False)
            self.sequence_id = seq.id
        if not self.refund_sequence_id:
            seq = self.create_sequence(refund=True)
            self.refund_sequence_id = seq.id

    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        for journal in self:
            if journal.sequence_id:
                sequence = journal.sequence_id._get_current_sequence()
                journal.sequence_number_next = sequence.number_next_actual
            else:
                journal.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        for journal in self:
            if journal.sequence_id and journal.sequence_number_next:
                sequence = journal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.sequence_number_next

    @api.depends('refund_sequence_id.use_date_range', 'refund_sequence_id.number_next_actual')
    def _compute_refund_seq_number_next(self):
        for journal in self:
            if journal.refund_sequence_id:
                sequence = journal.refund_sequence_id._get_current_sequence()
                journal.refund_sequence_number_next = sequence.number_next_actual
            else:
                journal.refund_sequence_number_next = 1

    def _inverse_refund_seq_number_next(self):
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence_number_next:
                sequence = journal.refund_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.refund_sequence_number_next

    @api.model
    def _get_sequence_prefix(self, code, refund=False):
        # Si se ha definido un prefijo DTE en el diario, úsalo;
        # de lo contrario, usa el código por defecto.
        prefix = None
        try:
            # 'self' en este contexto puede no tener el registro, usar defaults
            journal = self
            if hasattr(journal, 'dte_prefix') and journal.dte_prefix:
                prefix = journal.dte_prefix
        except Exception:
            prefix = None
        if not prefix:
            prefix = code.upper()
        if refund:
            prefix = 'R' + prefix
        # Añadir formato de rango de fecha si se requiere
        return prefix + '/%(range_year)s/'

    @api.model
    def create(self, vals):
        if not vals.get('sequence_id'):
            vals['sequence_id'] = self.sudo()._create_sequence(vals).id
        if not vals.get('refund_sequence_id'):
            vals['refund_sequence_id'] = self.sudo()._create_sequence(vals, refund=True).id
        return super(AccountJournal, self.with_context(mail_create_nolog=True)).create(vals)

    def write(self, vals):
        # Al cambiar code o mantener prefijo, actualizamos prefix de secuencia
        res = super(AccountJournal, self).write(vals)
        # Si se modificó dte_prefix, actualizar prefix de sequence_id
        if 'dte_prefix' in vals:
            for journal in self:
                new_pref = journal.dte_prefix or journal.code.upper()
                journal.sequence_id.write({'prefix': new_pref + '/%(range_year)s/'})
                if journal.refund_sequence_id:
                    journal.refund_sequence_id.write({'prefix': 'R' + new_pref + '/%(range_year)s/'})
        return res
