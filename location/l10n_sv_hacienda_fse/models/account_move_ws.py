6##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import pyqrcode

import pytz

# Definir la zona horaria de El Salvador
tz_el_salvador = pytz.timezone('America/El_Salvador')


import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"



######################################### FCE-EXPORTACION

    def sit_base_map_invoice_info_fse(self):
        _logger.info("SIT sit_base_map_invoice_info self = %s", self)

        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        _logger.info("SIT sit_base_map_invoice_info = %s", invoice_info)

        invoice_info["dteJson"] = self.sit__fse_base_map_invoice_info_dtejson()
        return invoice_info


    def sit__fse_base_map_invoice_info_dtejson(self):
        _logger.info("SIT sit_base_map_invoice_info_dtejson self = %s", self)
        invoice_info = {}
        invoice_info["identificacion"] = self.sit__fse_base_map_invoice_info_identificacion()
        _logger.info("SIT sit_base_map_invoice_info_dtejson = %s", invoice_info)
        invoice_info["emisor"] = self.sit__fse_base_map_invoice_info_emisor()
        invoice_info["sujetoExcluido"] = self.sit__fse_base_map_invoice_info_sujeto_excluido()
        cuerpoDocumento = self.sit_fse_base_map_invoice_info_cuerpo_documento()
        _logger.info("SIT Cuerpo documento =%s", cuerpoDocumento)
        invoice_info["cuerpoDocumento"] = cuerpoDocumento[0]
        _logger.info("SIT CUERTO_DOCUMENTO = %s",   invoice_info["cuerpoDocumento"] )
        if str(invoice_info["cuerpoDocumento"]) == 'None':
            raise UserError(_('La Factura no tiene linea de Productos Valida.'))        
        invoice_info["resumen"] = self.sit_fse_base_map_invoice_info_resumen()
        invoice_info["apendice"] = None
        return invoice_info        

    def sit__fse_base_map_invoice_info_identificacion(self):
        _logger.info("SIT sit_base_map_invoice_info_identificacion self = %s", self)
        invoice_info = {}
        invoice_info["version"] = 1
        validation_type = self._compute_validation_type_2()        
        param_type = self.env["ir.config_parameter"].sudo().get_param("afip.ws.env.type")
        if param_type:
            validation_type = param_type
        if validation_type == 'homologation': 
            ambiente = "00"
        else:
            ambiente = "01"        
        invoice_info["ambiente"] = ambiente
        invoice_info["tipoDte"] = self.journal_id.sit_tipo_documento.codigo
        if self.name == "/":
            tipo_dte = self.journal_id.sit_tipo_documento.codigo or '01'

            # Obtener el código de establecimiento desde el diario
            cod_estable = self.journal_id.cod_sit_estable or '0000M001'

            # Obtener la secuencia desde ir.sequence con padding 15
            correlativo = self.env['ir.sequence'].next_by_code('dte.secuencia') or '0'
            correlativo = correlativo.zfill(15)

            # Construir el número de control completo
            invoice_info["numeroControl"] = f"DTE-{tipo_dte}-0000{cod_estable}-{correlativo}"
        else:
            invoice_info["numeroControl"] = self.name
        _logger.info("SIT Número de control = %s (%s)", invoice_info["numeroControl"])
        _logger.info("SIT sit_base_map_invoice_info_identificacion0 = %s", invoice_info)
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()          #  company_id.sit_uuid.upper()
        invoice_info["tipoModelo"] = int(self.sit_modelo_facturacion)
        invoice_info["tipoOperacion"] = int(self.sit_tipo_transmision)
        tipoContingencia = int(self.sit_tipo_contingencia)
        invoice_info["tipoContingencia"] = tipoContingencia
        motivoContin = str(self.sit_tipo_contingencia_otro)
        invoice_info["motivoContin"] = motivoContin
        import datetime
        import pytz
        import os
        os.environ['TZ'] = 'America/El_Salvador'  # Establecer la zona horaria
        datetime.datetime.now() 
        salvador_timezone = pytz.timezone('America/El_Salvador')
        FechaEmi = datetime.datetime.now(salvador_timezone)
        _logger.info("SIT FechaEmi = %s (%s)", FechaEmi, type(FechaEmi))
        invoice_info["fecEmi"] = FechaEmi.strftime('%Y-%m-%d')
        invoice_info["horEmi"] = FechaEmi.strftime('%H:%M:%S')
        invoice_info["tipoMoneda"] =  self.currency_id.name
        if invoice_info["tipoOperacion"] == 1:
            invoice_info["tipoModelo"] = 1
            invoice_info["tipoContingencia"] = None
            invoice_info["motivoContin"] = None
        else:
            invoice_info["tipoModelo"] = 2
        if invoice_info["tipoOperacion"] == 2:
            invoice_info["tipoContingencia"] = tipoContingencia
        if invoice_info["tipoContingencia"] == 5:
            invoice_info["motivoContin"] = motivoContin
        _logger.info("SIT sit_fse_ base_map_invoice_info_identificacion1 = %s", invoice_info)
        return invoice_info

    def sit__fse_base_map_invoice_info_emisor(self):
        _logger.info("SIT sit__fse_base_map_invoice_info_emisor self = %s", self)
        invoice_info = {}
        direccion = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        nrc= self.company_id.company_registry
        if nrc:        
            nrc = nrc.replace("-", "")        
        invoice_info["nrc"] = nrc
        invoice_info["nombre"] = self.company_id.name
        invoice_info["codActividad"] = self.company_id.codActividad.codigo
        invoice_info["descActividad"] = self.company_id.codActividad.valores
        direccion["departamento"] =  self.company_id.state_id.code
        direccion["municipio"] =  self.company_id.munic_id.code
        direccion["complemento"] =  self.company_id.street
        _logger.info("SIT direccion self = %s", direccion)
        invoice_info["direccion"] = direccion
        if  self.company_id.phone:
            invoice_info["telefono"] =  self.company_id.phone
        else:
            invoice_info["telefono"] =  None
        invoice_info["correo"] =  self.company_id.email
        invoice_info["codEstableMH"] =  self.journal_id.sit_codestable
        invoice_info["codEstable"] =  self.journal_id.sit_codestable
        invoice_info["codPuntoVentaMH"] =  self.journal_id.sit_codpuntoventa
        invoice_info["codPuntoVenta"] =  self.journal_id.sit_codpuntoventa
        return invoice_info   

    def sit__fse_base_map_invoice_info_sujeto_excluido(self):
        _logger.info("SIT sit_base_map_invoice_info_receptor self = %s", self)
        direccion_rec = {}
        invoice_info = {}
       # Número de Documento (Nit)
        nit = self.partner_id.vat.replace("-", "") if self.partner_id.vat and isinstance(self.partner_id.vat, str) else None
        invoice_info["numDocumento"] = nit

        # Establece 'tipoDocumento' como None si 'nit' es None
        tipoDocumento = self.partner_id.l10n_latam_identification_type_id.codigo
        invoice_info["tipoDocumento"] = tipoDocumento
        nrc= self.partner_id.nrc
        if nrc:
            nrc = nrc.replace("-", "")        
        invoice_info["nombre"] = self.partner_id.name
        codActividad = self.partner_id.codActividad.codigo if self.partner_id.codActividad and hasattr(self.partner_id.codActividad, 'codigo') else None
        invoice_info["codActividad"] = codActividad
        descActividad = self.partner_id.codActividad.valores if self.partner_id.codActividad and hasattr(self.partner_id.codActividad, 'valores') else None
        invoice_info["descActividad"] = descActividad
        direccion_rec["departamento"] = self.partner_id.state_id.code
        direccion_rec["municipio"] =   self.partner_id.munic_id.code
        direccion_rec["complemento"] =  self.partner_id.street
        _logger.info("SIT direccion self = %s", direccion_rec)
        invoice_info["direccion"] = direccion_rec
        if self.partner_id.phone:
            invoice_info["telefono"] =  self.partner_id.phone
        else:
            invoice_info["telefono"] = None
        if self.partner_id.email:
            invoice_info["correo"] =  self.partner_id.email
        else:
            invoice_info["correo"] = None    
        return invoice_info        

    def sit_fse_base_map_invoice_info_cuerpo_documento(self):
            _logger.info("SIT sit_base_map_invoice_info_cuerpo_documento self = %s", self)

            lines = []
            _logger.info("SIT sit_base_map_invoice_info_cuerpo_documento self = %s", self.invoice_line_ids)

            # for line in self.invoice_line_ids.filtered(lambda x: not x.display_type):
            item_numItem = 0
            total_Gravada = 0.0
            totalIva = 0.0
            for line in self.invoice_line_ids:     
                item_numItem += 1       
                line_temp = {}
                lines_tributes = []
                line_temp["numItem"] = item_numItem
                tipoItem = int(line.product_id.tipoItem.codigo or line.product_id.product_tmpl_id.tipoItem.codigo)
                line_temp["tipoItem"] = tipoItem
                line_temp["cantidad"] = line.quantity
                line_temp["codigo"] = line.product_id.default_code
                # unidad de referencia del producto si se comercializa
                # en una unidad distinta a la de consumo
                # uom is not mandatory, if no UOM we use "unit"
                codTributo = line.product_id.tributos_hacienda_cuerpo.codigo
                # if codTributo == False:
                #     line_temp["codTributo"] = None
                # else:
                #     line_temp["codTributo"] = line.product_id.tributos_hacienda_cuerpo.codigo
                _logger.info("SIT UOM =%s",  line.product_id.uom_hacienda)
                if not line.product_id.uom_hacienda:
                    uniMedida = 7
                    raise UserError(
                        _("UOM de producto no configurado para:  %s" % (line.product_id.name))
                    )
                else:
                    _logger.info("SIT uniMedida self = %s",  line.product_id)
                    _logger.info("SIT uniMedida self = %s",  line.product_id.uom_hacienda)

                    uniMedida = int(line.product_id.uom_hacienda.codigo)
                line_temp["uniMedida"] = int(uniMedida)

                line_temp["descripcion"] = line.name
                line_temp["precioUni"] = round(line.price_unit,2)
                # line_temp["importe"] = line.price_subtotal
                # calculamos bonificacion haciendo teorico menos importe

                line_temp["montoDescu"] = (
                    line_temp["cantidad"]  * (line.price_unit * (line.discount / 100))
                    
                    or 0.0
                )
                codigo_tributo_codigo=None
                codigo_tributo=None
                for line_tributo in line.tax_ids:
                    codigo_tributo_codigo = line_tributo.tributos_hacienda.codigo
                    codigo_tributo = line_tributo.tributos_hacienda
                lines_tributes.append(codigo_tributo_codigo)
                # line_temp["tributos"] = lines_tributes
                vat_taxes_amounts = line.tax_ids.compute_all(
                    line.price_unit,
                    self.currency_id,
                    line.quantity,
                    product=line.product_id,
                    partner=self.partner_id,
                )
                if vat_taxes_amounts['taxes']:
                    _logger.info("SIT vat_taxes_amounts 0=%s", vat_taxes_amounts['taxes'][0])
                    vat_taxes_amount = vat_taxes_amounts['taxes'][0]['amount']
                    sit_amount_base = round(vat_taxes_amounts['taxes'][0]['base'], 2)
                else:
                    # Manejar el caso donde no hay impuestos
                    vat_taxes_amount = 0
                    sit_amount_base = round(line.quantity * line.price_unit, 2)
                compraS = line_temp["cantidad"] * (line.price_unit - (line.price_unit * (line.discount / 100)))
                line_temp["compra"] = round(compraS,2)

                totalIva += 0

                lines.append(line_temp)
                self.check_parametros_linea_firmado(line_temp)
            return lines, codigo_tributo, total_Gravada, float(totalIva)

    def sit_fse_base_map_invoice_info_resumen(self):
        _logger.info("SIT sit_base_map_invoice_info_resumen self = %s", self)
        invoice_info = {}
        invoice_info["totalCompra"] = round(self.amount_total, 2 )
        invoice_info["descu"] = 0
        invoice_info["totalDescu"] = 0
        invoice_info["subTotal"] = round(self.amount_total, 2 )
        invoice_info["ivaRete1"] = 0
        invoice_info["reteRenta"] = 0
        invoice_info["totalPagar"] = round(self.amount_total, 2 )
        invoice_info["totalLetras"] = self.amount_text
        invoice_info["condicionOperacion"] = int(self.condiciones_pago)
        invoice_info["observaciones"] = None
        pagos = {}  # Inicializa el diccionario pagos
        pagos["codigo"] = self.forma_pago.codigo  # '01'   # CAT-017 Forma de Pago    01 = bienes
        pagos["montoPago"] = round(self.amount_total, 2)
        pagos["referencia"] = None  # Un campo de texto llamado Referencia de pago
        if int(self.condiciones_pago) in [2]:
            pagos["plazo"] = self.sit_plazo.codigo   
            pagos["periodo"] = self.sit_periodo   #30      #  Es un nuevo campo entero
            invoice_info["pagos"] = [pagos]  # Asigna pagos como un elemento de una lista
        else:
            # pagos["plazo"] = self.sit_plazo.codigo 
            pagos["plazo"] = None    # Temporal
            pagos["periodo"] = None   #30      #  Es un nuevo campo entero            
        invoice_info["pagos"] = [pagos]  # por ahora queda en null.
        return invoice_info        
    
    def sit_obtener_payload_fse_dte_info(self,  ambiente, doc_firmado):
        _logger.info("SIT sit_obtener_payload_exp_dte_info self = %s", self)
        invoice_info = {}
        nit = self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["ambiente"] = ambiente
        invoice_info["idEnvio"] = 1
        invoice_info["version"] = 1
        invoice_info["documento"] = doc_firmado
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()
        return invoice_info      

    def sit_generar_uuid(self):
        import uuid
        # Genera un UUID versión 4 (basado en números aleatorios)
        uuid_aleatorio = uuid.uuid4()
        uuid_cadena = str(uuid_aleatorio)
        return uuid_cadena.upper()
