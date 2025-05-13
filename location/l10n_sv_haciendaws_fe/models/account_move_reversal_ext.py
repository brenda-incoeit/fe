from odoo import models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def refund_moves_custom(self):
        self.ensure_one()
        _logger.info("SIT refund_moves_custom iniciado con move_ids=%s", self.move_ids)

        if not self.journal_id:
            raise UserError(_("Debe seleccionar un diario antes de continuar."))

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_journal_id': self.journal_id.id,
            'dte_name_preassigned': True,
        })
        _logger.info("SIT refund_moves_custom usando contexto: %s", ctx)

        moves = self.move_ids
        default_values_list = []

        for move in moves:
            default_vals = self._prepare_default_reversal(move)
            default_vals['journal_id'] = self.journal_id.id
            default_vals['move_type'] = 'out_refund'

            # Generar número de control sin guardar aún
            move_temp = self.env['account.move'].new(default_vals)
            move_temp.journal_id = self.journal_id
            nombre_generado = move_temp._generate_dte_name()

            if not nombre_generado:
                raise UserError(_("No se pudo generar un número de control para el documento."))

            # Pasar el nombre generado directamente en los vals
            default_vals['name'] = nombre_generado
            _logger.info("SIT Nombre de control válido (preview, no guardado): %s", nombre_generado)

            default_values_list.append(default_vals)

        new_moves = self.env['account.move'].with_context(ctx).create(default_values_list)

        return {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form' if len(new_moves) == 1 else 'list,form',
            'res_id': new_moves.id if len(new_moves) == 1 else False,
            'domain': [('id', 'in', new_moves.ids)],
            'context': {'default_move_type': new_moves[0].move_type if new_moves else 'out_refund'},
        }

