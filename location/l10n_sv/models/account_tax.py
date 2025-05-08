##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_repr
from odoo.addons.l10n_sv_haciendaws_fe.afip_utils import get_invoice_number_from_response
import logging

_logger = logging.getLogger(__name__)


class Sit_AccountTax(models.Model):
    _inherit = "account.tax"

    tributos_hacienda = fields.Many2one("account.move.tributos.field", string="Tributos - Hacienda" )
    tributos_hacienda_resumen_dte = fields.Many2one("account.move.tributos.field", string="Tributos Resumen DTE- Hacienda" , domain = "[('sit_aplicados_a','=',1)]" )
    tributos_hacienda_cuerpo = fields.Many2one("account.move.tributos.field", string="Tributos Cuerpo- Hacienda" , domain = "[('sit_aplicados_a','=',2)]" )
    tributos_hacienda_resumen_documento = fields.Many2one("account.move.tributos.field", string="Tributos Resumen Documento - Hacienda" , domain = "[('sit_aplicados_a','=',3)]" )

class Sit_AccountTax_extended(models.Model):
    _inherit = "account.move.tributos.field"

    def name_get(self):
        result = []
        for tax in self:
            tax_hacienda = '(%s) %s' % (tax.codigo, tax.valores)
            _logger.info("SIT tax_hacienda = %s", tax_hacienda)
            _logger.info("SIT tax_hacienda0 = %s", tax.id)
            result.append((tax.id, tax_hacienda))
            _logger.info("SIT result = %s", result)
        return result