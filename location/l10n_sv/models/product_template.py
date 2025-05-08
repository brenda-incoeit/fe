# -*- coding: utf-8 -*-
from odoo import fields, models, api


class sit_product_template(models.Model):
    
    _inherit = 'product.template'
    uom_hacienda = fields.Many2one('account.move.unidad_medida.field')
    tipoItem = fields.Many2one('account.move.tipo_item.field', string="Tipo de Item")
    sit_psv = fields.Float("Precio sugerido de Venta", default=0.0)
    tributos_hacienda_cuerpo = fields.Many2one("account.move.tributos.field", string="Tributos Cuerpo- Hacienda" , domain = "[('sit_aplicados_a','=',2)]" )

class sit_product_product(models.Model):
    
    _inherit = 'product.product'
    tipoItem = fields.Many2one('account.move.tipo_item.field', string="Tipo de Item")
    sit_psv = fields.Float("Precio sugerido de Venta", default=0.0)
    tributos_hacienda_cuerpo = fields.Many2one("account.move.tributos.field", string="Tributos Cuerpo- Hacienda" , domain = "[('sit_aplicados_a','=',2)]" )
