# -*- coding: utf-8 -*-
from odoo import fields, models, api


class sit_account_move(models.Model):
    
    _inherit = 'account.move'
    forma_pago = fields.Many2one('account.move.forma_pago.field')
    invoice_payment_term_name = fields.Char(related='invoice_payment_term_id.name')
    condiciones_pago = fields.Selection(
        selection='_get_condiciones_pago_selection', string='Condición de la Operación (Pago) - Hacienda')
    sit_plazo = fields.Many2one('account.move.plazo.field', string="Plazos")
    sit_periodo = fields.Integer(string="Periodo")

    sit_tipo_contingencia = fields.Many2one('account.move.tipo_contingencia.field', string="Tipo de Contingencia")
    sit_tipo_contingencia_otro = fields.Text(string="Especifique el Otro Tipo de Contingencia")
    sit_tipo_contingencia_valores = fields.Char(related="sit_tipo_contingencia.valores", string="Tipo de contingiancia(nombre)")
    sit_modelo_facturacion = fields.Selection(
        selection='_get_modelo_facturacion_selection', string='Modelo de Facturacion - Hacienda')
    sit_tipo_transmision = fields.Selection(
        selection='_get_tipo_transmision_selection', string='Tipo de Transmisión - Hacienda')
    sit_referencia = fields.Text(string="Referencia", default="")
    sit_qr_hacienda = fields.Binary("QR Hacienda", default=False) 
    sit_json_respuesta = fields.Text("Json de Respuesta", default="") 

    def _get_condiciones_pago_selection(self):
        return [
            ('1', '1-Contado'),
            ('2', '2-A Crédito'),
            ('3', '3-Otro'),
        ]

    def _get_modelo_facturacion_selection(self):
        return [
            ('1', 'Modelo Facturación previo'),
            ('2', 'Modelo Facturación diferido'),
        ]
    def _get_tipo_transmision_selection(self):
        return [
            ('1', 'Transmisión normal'),
            ('2', 'Transmisión por contingencia'),
        ]    
    
    @api.onchange('condiciones_pago')
    def change_sit_plazo(self):
        if self.condiciones_pago == 1:
            self.sit_plazo = None

