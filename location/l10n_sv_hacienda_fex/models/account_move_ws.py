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

    def sit_base_map_invoice_info_fex(self):
        _logger.info("SIT sit_base_map_invoice_info self = %s", self)

        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        _logger.info("SIT sit_base_map_invoice_info = %s", invoice_info)

        invoice_info["dteJson"] = self.sit__fex_base_map_invoice_info_dtejson()
        return invoice_info


    def sit__fex_base_map_invoice_info_dtejson(self):
        _logger.info("SIT sit_base_map_invoice_info_dtejson self = %s", self)
        invoice_info = {}
        invoice_info["identificacion"] = self.sit__fex_base_map_invoice_info_identificacion()
        _logger.info("SIT sit_base_map_invoice_info_dtejson = %s", invoice_info)
        invoice_info["emisor"] = self.sit__fex_base_map_invoice_info_emisor()
        invoice_info["receptor"] = self.sit__fex_base_map_invoice_info_receptor()
        invoice_info["otrosDocumentos"] = None
        invoice_info["ventaTercero"] = None
        cuerpoDocumento = self.sit_fex_base_map_invoice_info_cuerpo_documento()
        _logger.info("SIT Cuerpo documento =%s", cuerpoDocumento)
        invoice_info["cuerpoDocumento"] = cuerpoDocumento[0]
        _logger.info("SIT CUERTO_DOCUMENTO = %s",   invoice_info["cuerpoDocumento"] )
        if str(invoice_info["cuerpoDocumento"]) == 'None':
            raise UserError(_('La Factura no tiene linea de Productos Valida.'))        
        invoice_info["resumen"] = self.sit_fex_base_map_invoice_info_resumen()
        invoice_info["apendice"] = None
        return invoice_info        

    def sit__fex_base_map_invoice_info_identificacion(self):
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
        _logger.info("SIT sit_fex_base_map_invoice_info_identificacion0 = %s", invoice_info)
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()          #  company_id.sit_uuid.upper()
        invoice_info["tipoModelo"] = int(self.sit_modelo_facturacion)
        invoice_info["tipoOperacion"] = int(self.sit_tipo_transmision)
        invoice_info["tipoContingencia"] = None
        invoice_info["motivoContigencia"] = None
        _logger.info("SIT sit_fex_base_map_invoice_info_identificacion0 = %s", invoice_info)

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
        _logger.info("SIT sit_fex_ base_map_invoice_info_identificacion1 = %s", invoice_info)
        return invoice_info


    def sit__fex_base_map_invoice_info_emisor(self):
        _logger.info("SIT sit__fex_base_map_invoice_info_emisor self = %s", self)
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
        if  self.company_id.nombreComercial:
            invoice_info["nombreComercial"] = self.company_id.nombreComercial
        else:
            invoice_info["nombreComercial"] = None
        invoice_info["tipoEstablecimiento"] =  self.company_id.tipoEstablecimiento.codigo
        _logger.info("SIT departamento self = %s", self.company_id.state_id)
        _logger.info("SIT municipio self = %s", self.company_id.munic_id)
        
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
        invoice_info["tipoItemExpor"] =  1
        invoice_info["recintoFiscal"] =  '99'
        invoice_info["regimen"] =  'EX1.1000.000'

        return invoice_info   

    def sit__fex_base_map_invoice_info_receptor(self):
        _logger.info("SIT sit_base_map_invoice_info_receptor self = %s", self)
        
        invoice_info = {}
         # Número de Documento (Nit)
        nit = self.partner_id.vat.replace("-", "") if self.partner_id.vat and isinstance(self.partner_id.vat, str) else None
        invoice_info["numDocumento"] = nit

        # Establece 'tipoDocumento' como None si 'nit' es None
        tipoDocumento = self.partner_id.l10n_latam_identification_type_id.codigo if self.partner_id.l10n_latam_identification_type_id and nit else None
        invoice_info["tipoDocumento"] = tipoDocumento
        invoice_info["nombre"] = self.partner_id.name
        invoice_info["codPais"] = '9483'
        invoice_info["nombrePais"] = 'Guatemala'        
        if self.partner_id.company_type == 'person':
            tipoPersona = 1
        elif self.partner_id.company_type == 'company':
            tipoPersona = 2
        invoice_info["tipoPersona"] = tipoPersona
        if  self.partner_id.nombreComercial:
            invoice_info["nombreComercial"] = self.partner_id.nombreComercial
        else:
            invoice_info["nombreComercial"] = None
        descActividad = self.partner_id.codActividad.valores if self.partner_id.codActividad and hasattr(self.partner_id.codActividad, 'valores') else None
        invoice_info["descActividad"] = descActividad    
        invoice_info["complemento"] =  self.partner_id.street
        if self.partner_id.phone:
            invoice_info["telefono"] =  self.partner_id.phone
        else:
            invoice_info["telefono"] = None
        if self.partner_id.email:
            invoice_info["correo"] =  self.partner_id.email
        else:
            invoice_info["correo"] = None    
        return invoice_info        

    def sit_fex_base_map_invoice_info_cuerpo_documento(self):
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
            line_temp["codigo"] = line.product_id.default_code
            line_temp["descripcion"] = line.name
            line_temp["cantidad"] = line.quantity
            _logger.info("SIT UOM =%s",  line.product_id.uom_hacienda)
            if not line.product_id.uom_hacienda:
                uniMedida = 7
                raise UserError(
                    _("UOM de producto no configurado para:  %s" % (line.product_id.name)))
            else:
                _logger.info("SIT uniMedida self = %s",  line.product_id)
                _logger.info("SIT uniMedida self = %s",  line.product_id.uom_hacienda)
                uniMedida = int(line.product_id.uom_hacienda.codigo)
            line_temp["uniMedida"] = int(uniMedida)
            line_temp["precioUni"] = round(line.price_unit, 4)
            line_temp["montoDescu"] = (
                round(line_temp["cantidad"]  * (line.price_unit * (line.discount / 100))/1.13,2)
                or 0.0
            )
            ventaGravada =  round(line_temp["cantidad"]  * (line.price_unit - (line.discount / 100)),2)
            line_temp["ventaGravada"] = ventaGravada
            codigo_tributo_codigo=None
            codigo_tributo = None
            for line_tributo in line.tax_ids:
                codigo_tributo_codigo = line_tributo.tributos_hacienda.codigo
                codigo_tributo = line_tributo.tributos_hacienda
            lines_tributes.append(codigo_tributo_codigo)
            if lines_tributes == None:
                line_temp["tributos"] = lines_tributes
            else:
                line_temp["tributos"] = None
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
            # _logger.info("SIT vat_taxes_ammounts 0=%s", vat_taxes_amounts['taxes'][0])
            # _logger.info("SIT vat_taxes_ammounts 1=%s", vat_taxes_amounts['taxes'][0]['amount'])
            # _logger.info("SIT sit_amount_base 1=%s", vat_taxes_amounts['taxes'][0]['base'])
            # vat_taxes_amount =  vat_taxes_amounts['taxes'][0]['amount']
            # sit_amount_base = round( vat_taxes_amounts['taxes'][0]['base'], 2 )    # = subtotal - iva
            line_temp["noGravado"] = 0.0           #<line.price_unit <--------------  Temporal Null
            price_unit_mas_iva = round(line.price_unit, 4)  # Redondea line.price_unit a 4 decimales
            if line_temp["cantidad"] > 0:
                price_unit = round(sit_amount_base / line_temp["cantidad"], 4)  # Redondea el resultado a 4 decimales
            else:
                price_unit = round(0.00, 4)  # Si line_temp["cantidad"] es cero, redondea a 4 decimales
            line_temp["precioUni"] = price_unit
            _logger.info("SITX_X_X_X_X_X_XX_X_X_X_X_X_XX_ amountBase=%s", sit_amount_base)
            ventaGravada = round(((sit_amount_base)-(line.price_unit * (line.discount / 100))), 2)
            # ventaGravada = round((line_temp["cantidad"] * (line.price_unit - (line.price_unit * (line.discount / 100)))) / 1.13, 2)
            total_Gravada +=  ventaGravada
            _logger.info("SITX_X_X_X_X_X_XX_X_X_X_X_X_XX_ ventaGravada=%s", ventaGravada)
            line_temp["ventaGravada"] = ventaGravada           
            totalIva += round(vat_taxes_amount - ((((line.price_unit * line.quantity) * (line.discount / 100))/1.13)*0.13),2)
            _logger.info("SIT totalIVA ______0 =%s", totalIva)
            lines.append(line_temp)
            self.check_parametros_linea_firmado(line_temp)
        _logger.info("SIT totalIVA ______1 =%s", totalIva)
        return lines, codigo_tributo, total_Gravada, line.tax_ids, totalIva

    def sit_fex_base_map_invoice_info_resumen(self):
        _logger.info("SIT sit_base_map_invoice_info_resumen self = %s", self)
        invoice_info = {}
        invoice_info["totalGravada"] = round(self.amount_total, 2 )
        invoice_info["totalNoGravado"] = 0
        invoice_info["descuento"] = 0
        invoice_info["porcentajeDescuento"] = 0
        invoice_info["totalDescu"] = 0
        invoice_info["montoTotalOperacion"] = round(self.amount_total, 2 )
        invoice_info["totalPagar"] = round(self.amount_total, 2 )
        invoice_info["totalLetras"] = self.amount_text
        invoice_info["condicionOperacion"] = int(self.condiciones_pago)
        pagos = {}  # Inicializa el diccionario pagos
        pagos["codigo"] = self.forma_pago.codigo  # '01'   # CAT-017 Forma de Pago    01 = bienes
        pagos["montoPago"] = round(self.amount_total, 2)
        pagos["referencia"] = None  # Un campo de texto llamado Referencia de pago
        invoice_info["codIncoterms"] = '10'
        invoice_info["descIncoterms"] = 'CFR-Costo y flete'
        invoice_info["observaciones"] = None
        invoice_info["flete"] = 0
        invoice_info["numPagoElectronico"] = None
        invoice_info["seguro"] = 0
        
        if int(self.condiciones_pago) in [2]:
            pagos["plazo"] = self.sit_plazo.codigo   
            pagos["periodo"] = self.sit_periodo   #30      #  Es un nuevo campo entero
            invoice_info["pagos"] = [pagos]  # Asigna pagos como un elemento de una lista
        else:
            # pagos["plazo"] = self.sit_plazo.codigo 
            pagos["plazo"] = None    # Temporal
            pagos["periodo"] = None   #30      #  Es un nuevo campo entero            
            invoice_info["pagos"] = None   # por ahora queda en null.
        return invoice_info        

    def sit_obtener_payload_fex_dte_info(self,  ambiente, doc_firmado):
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
