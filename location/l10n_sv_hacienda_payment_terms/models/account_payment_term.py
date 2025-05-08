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

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    condiciones_pago = fields.Selection(
        selection='_get_condiciones_pago_selection', string='Condición de la Operación (Pago) - Hacienda')
    sit_plazo = fields.Many2one('account.move.plazo.field', string="Plazos")
    sit_periodo = fields.Integer(string="Periodo")

    def _get_condiciones_pago_selection(self):
        return [
            ('1', '1-Contado'),
            ('2', '2-A Crédito'),
            ('3', '3-Otro'),
        ]

