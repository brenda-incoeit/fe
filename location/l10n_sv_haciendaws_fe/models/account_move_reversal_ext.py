from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type',
        string='Tipo de Documento',
        domain=[('code', '=', '05')],
    )

    def refund_moves_custom(self):
        self.ensure_one()
        _logger.info("SIT refund_moves_custom iniciado con move_ids=%s", self.move_ids)

        if not self.journal_id:
            raise UserError(_("Debe seleccionar un diario antes de continuar."))

        if self.journal_id.type == 'sale' and not self.l10n_latam_document_type_id:
            raise UserError(_("Debe seleccionar un Tipo de Documento para la Nota de Crédito."))

        if self.journal_id.type == 'sale' and not self.l10n_latam_document_type_id:
            doc_type = self.env['l10n_latam.document.type'].search([('code', '=', '05')], limit=1)
            if not doc_type:
                raise UserError(_("No se encontró el tipo de documento (05) Nota de crédito."))
            self.l10n_latam_document_type_id = doc_type

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_journal_id': self.journal_id.id,
            'default_l10n_latam_document_type_id': self.l10n_latam_document_type_id.id,
            'dte_name_preassigned': True,
        })
        _logger.info("SIT refund_moves_custom usando contexto: %s", ctx)

        moves = self.move_ids
        default_values_list = []

        for move in moves:
            default_vals = self._prepare_default_reversal(move)
            default_vals['journal_id'] = self.journal_id.id
            default_vals['move_type'] = 'out_refund'
            default_vals['partner_id'] = move.partner_id.id
            default_vals['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id

            default_vals['inv_refund_id'] = move.id
            default_vals['reversed_entry_id'] = move.id

            _logger.info("SIT Preparing reversal for move_id=%s → reversed_entry_id=%s | inv_refund_id=%s",
                         move.id, default_vals['reversed_entry_id'], default_vals['inv_refund_id'])

            invoice_lines_vals = []
            _logger.info("SIT Invoice Lines: %s", move.invoice_line_ids)

            for line in move.invoice_line_ids:
                _logger.info("SIT display type: %s", line.display_type)
                if line.display_type not in [False, 'product']:
                    continue
                invoice_lines_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'account_id': line.account_id.id,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                }))
                #'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False,
                #'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
            default_vals['invoice_line_ids'] = invoice_lines_vals
            _logger.info("SIT listado de productos=%s", default_vals['invoice_line_ids'])

            if not move.name or move.name == '/' or not move.name.startswith("DTE-"):
                move_temp = self.env['account.move'].new(default_vals)
                move_temp.journal_id = self.journal_id
                nombre_generado = move_temp._generate_dte_name()

                if not nombre_generado:
                    raise UserError(_("No se pudo generar un número de control para el documento."))

                default_vals['name'] = nombre_generado
                _logger.info("SIT Nombre generado para NC: %s", nombre_generado)
            else:
                _logger.info("SIT Usando nombre original: %s", move.name)

            default_values_list.append(default_vals)

        # Log antes de crear
        for i, val in enumerate(default_values_list):
            _logger.info("SIT Pre-creación NC #%s: reversed_entry_id=%s | inv_refund_id=%s | name=%s",
                         i, val.get('reversed_entry_id'), val.get('inv_refund_id'), val.get('name'))

        new_moves = self.env['account.move'].with_context(ctx).create(default_values_list)

        for move in new_moves:
            _logger.info("SIT NC creada: ID=%s | reversed_entry_id=%s | inv_refund_id=%s | name=%s",
                         move.id, move.reversed_entry_id.id, move.inv_refund_id.id, move.name)

        return {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form' if len(new_moves) == 1 else 'list,form',
            'res_id': new_moves.id if len(new_moves) == 1 else False,
            'domain': [('id', 'in', new_moves.ids)],
            'context': {
                'default_move_type': new_moves[0].move_type if new_moves else 'out_refund',
            },
        }
