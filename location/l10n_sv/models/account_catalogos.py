from odoo import models, api, fields, _
from ast import literal_eval
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class sit_CAT_002_tipo_documento(models.Model):
    _name = "account.journal.tipo_documento.field"
    _description = "HACIENDA tipo de Documento"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")

class sit_CAT_003_tipo_modelo(models.Model):
    _name = "account.journal.tipo_modelo.field"
    _description = "HACIENDA tipo de Modelo"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")

class sit_CAT_005_tipo_contingencia(models.Model):
    _name = "account.move.tipo_contingencia.field"
    _description = "HACIENDA tipo de contingencia"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")   


class sit_CAT_009_tipo_establecimiento(models.Model):
    _name = "account.move.tipo_establecimiento.field"
    _description = "HACIENDA tpo de establecimiento"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")

 

class sit_CAT_011_tipo_item(models.Model):
    _name = "account.move.tipo_item.field"
    _description = "HACIENDA tpo de Item"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")


class sit_CAT_014_unidad_medida_Field(models.Model):
    _name = "account.move.unidad_medida.field"
    _description = "HACIENDA Unidad de Medida"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")

class sit_CAT_015_tributos_Field(models.Model):
    _name = "account.move.tributos.field"
    _description = "HACIENDA Tributos"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")

    sit_aplicados_a = fields.Selection(
        selection='_get_aplicados_a', string='Aplicados a')

    def _get_aplicados_a(self):
        return [
            ('1', 'al resumen del dte'),
            ('2', 'al cuerpo del documento'),
            ('3', 'al resumen del documento'),
        ]











class sit_CAT_017_forma_pago_Field(models.Model):
    _name = "account.move.forma_pago.field"
    _description = "HACIENDA Forma de Pago"
    _rec_name = "valores"
    codigo = fields.Char("Código")
    valores = fields.Char("Valores")


class sit_CAT_018_plazo_Field(models.Model):
    _name = "account.move.plazo.field"
    _description = "HACIENDA Plazo"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")    

# class sit_CAT_018_plazo_Field(models.Model):
#     _name = "account.move.plazo.field"
#     _description = "HACIENDA Plazo"
#     _rec_name = "valores"

#     codigo = fields.Char("Código")
#     valores = fields.Char("Valores")    

class sit_CAT_019_actividad_economica_Field(models.Model):
    _name = "account.move.actividad_economica.field"
    _description = "HACIENDA Actividad Económica"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_021_otros_documentos_asociados_Field(models.Model):
    _name = "account.move.otros_documentos.field"
    _description = "HACIENDA Otros Docuemntos Asociados"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_023_tipo_documentos_contingencia_Field(models.Model):
    _name = "account.move.tipo_documento_contingencia.field"
    _description = "HACIENDA Tipo de documento de contingencia"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_024_tipo_invalidacion_Field(models.Model):
    _name = "account.move.tipo_invalidacion.field"
    _description = "HACIENDA Tipo de invalidación"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_025_titulo_rem_bienes_Field(models.Model):
    _name = "account.move.titulo_rem_bienes.field"
    _description = "HACIENDA Titulo a que se remiten los bienes"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        


class sit_CAT_026_tipo_donacion_Field(models.Model):
    _name = "account.move.tipo_donacion.field"
    _description = "HACIENDA Tipo de Donación"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_027_recinto_fiscal_Field(models.Model):
    _name = "account.move.recinto_fiscal.field"
    _description = "HACIENDA Recinto Fiscal"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_028_regimen_Field(models.Model):
    _name = "account.move.regimen.field"
    _description = "HACIENDA Régimen"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_029_tipo_persona_Field(models.Model):
    _name = "account.move.tipo_persona.field"
    _description = "HACIENDA Tipo de Persona"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_030_transporte_Field(models.Model):
    _name = "account.move.transporte.field"
    _description = "HACIENDA Transporte"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class sit_CAT_031_incoterms_Field(models.Model):
    _name = "account.move.incoterms.field"
    _description = "HACIENDA INCOTERMS"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        


class sit_CAT_032_domicilio_fiscal_Field(models.Model):
    _name = "account.move.domicilio_fiscal.field"
    _description = "HACIENDA Domicilio Fiscal"
    _rec_name = "valores"

    codigo = fields.Char("Código")
    valores = fields.Char("Valores")        

class SitCatTipoOperacion(models.Model):
    _name = 'account.move.tipo_operacion.field'
    _description = 'CAT - Tipo de Operación'
    _rec_name = "valores"

    codigo = fields.Char(string='Código')
    valores = fields.Char("Valores")

