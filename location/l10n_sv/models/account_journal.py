# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountJournal(models.Model):

    _inherit = "account.journal"

    company_partner = fields.Many2one('res.partner', related='company_id.partner_id')
    l10n_ar_afip_pos_partner_id = fields.Many2one(
        'res.partner', 'Dirección PdV Hacienda', help='Este es la dirección usada para los reportes de factura de este PdV',
        domain="['|', ('id', '=', company_partner), '&', ('id', 'child_of', company_partner), ('type', '!=', 'contact')]"
    )

    l10n_ar_sequence_ids = fields.One2many('ir.sequence', 'l10n_latam_journal_id', string="Secuencias")
    # Requerido de acuerto al catálogo 02
    # code_cat02 = fields.Char("Código del tipo DTE (CAT02)")
    sit_tipo_documento = fields.Many2one('account.journal.tipo_documento.field', 'Tipo de Documento (CAT02)', help='Tipo de Documento de acuerdo al CAT02' )
    sit_tipo_establecimiento = fields.Many2one('account.move.tipo_establecimiento.field', 'Tipo de Establecimiento (CAT09)', help='Tipo de Establecimiento al CAT09' )
    sit_codigo_tipo_establecimiento = fields.Char(related='sit_tipo_establecimiento.codigo', string='Codigo del Tipo de Establecimiento (CAT09)', help='Código del Tipo de Establecimiento al CAT09' )
    sit_codestable = fields.Char(string='codEstable' )
    sit_codpuntoventa = fields.Char(string='codPuntoVenta' )
    sit_modelo_facturacion = fields.Many2one('account.journal.tipo_modelo.field', 'Tipo de Modelo (CAT03)', help='Tipo de Modelo de acuerdo al CAT03')
    sit_tipo_transmision = fields.Many2one('account.move.tipo_operacion.field', string="Tipo de Operación (CAT04)", help='Código del Tipo de Operación al CAT004')
