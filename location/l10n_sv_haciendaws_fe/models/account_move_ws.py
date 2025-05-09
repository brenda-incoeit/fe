##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import pyqrcode
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"


##------ FEL-COMPROBANTE CREDITO FISCAL----------##

    def sit__ccf_base_map_invoice_info(self):
        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        invoice_info["dteJson"] = self.sit__ccf_base_map_invoice_info_dtejson()
        return invoice_info

    def sit__ccf_base_map_invoice_info_dtejson(self):
        invoice_info = {}
        invoice_info["identificacion"] = self.sit__ccf_base_map_invoice_info_identificacion()
        invoice_info["documentoRelacionado"] = None    #   self.sit__ccf_base_map_invoice_info_documentoRelacionado()
        invoice_info["emisor"] = self.sit__ccf_base_map_invoice_info_emisor()
        invoice_info["receptor"] = self.sit__ccf_base_map_invoice_info_receptor()
        invoice_info["otrosDocumentos"] = None
        invoice_info["ventaTercero"] = None
        cuerpoDocumento = self.sit_ccf_base_map_invoice_info_cuerpo_documento()
        invoice_info["cuerpoDocumento"] = cuerpoDocumento[0]
        if str(invoice_info["cuerpoDocumento"]) == 'None':
            raise UserError(_('La Factura no tiene linea de Productos Valida.'))        
        invoice_info["resumen"] = self.sit_ccf_base_map_invoice_info_resumen(cuerpoDocumento[2], cuerpoDocumento[3], cuerpoDocumento[4],  invoice_info["identificacion"]  )
        invoice_info["extension"] = self.sit_ccf_base_map_invoice_info_extension()
        invoice_info["apendice"] = None
        return invoice_info

    def sit__ccf_base_map_invoice_info_identificacion(self):
        invoice_info = {}
        invoice_info["version"] = 3

        _logger.info("SIT Identificacion CCF — nombre control: %s", self.name)

        # ——————————————————————
        # Ambiente y validación
        validation_type = self._compute_validation_type_2()
        param_type = self.env["ir.config_parameter"].sudo().get_param("afip.ws.env.type")
        if param_type:
            validation_type = param_type
        ambiente = "00" if validation_type == "homologation" else "01"
        invoice_info["ambiente"] = ambiente
        invoice_info["tipoDte"] = self.journal_id.sit_tipo_documento.codigo

        # ——————————————————————
        # Siempre usamos el name que ya tiene el DTE
        numero = (self.name or "").strip()
        if not numero.startswith("DTE-"):
            raise UserError(_("Número de control inválido: %s") % numero)

        invoice_info["numeroControl"] = numero

        # ——————————————————————
        # Extraemos tipoDte, codEstable y correlativo
        tipo_dte = cod_estable = correlativo = None
        if numero.startswith("DTE-"):
            parts = numero.split("-", 3)
            if len(parts) == 4:
                tipo_dte, cod_estable, correlativo = parts[1], parts[2], parts[3]
            else:
                _logger.warning("SIT Formato inesperado en numeroControl: %s", numero)
        else:
            _logger.warning("SIT numeroControl no comienza con 'DTE-': %s", numero)

        # ——————————————————————
        # UUID, modelo y operación (del diario)
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()
        invoice_info["tipoModelo"]       = int(self.journal_id.sit_modelo_facturacion)
        invoice_info["tipoOperacion"]    = int(self.journal_id.sit_tipo_transmision)

        # ——————————————————————
        # Contingencia y motivo
        invoice_info["tipoContingencia"] = int(self.sit_tipo_contingencia or 0)
        invoice_info["motivoContin"]     = str(self.sit_tipo_contingencia_otro or "")

        # ——————————————————————
        # Fecha y hora de emisión
        import datetime, pytz, os
        os.environ["TZ"] = "America/El_Salvador"  # Establecer la zona horaria
        now = datetime.datetime.now(pytz.timezone("America/El_Salvador"))
        invoice_info["fecEmi"] = now.strftime("%Y-%m-%d")
        invoice_info["horEmi"] = now.strftime("%H:%M:%S")

        invoice_info["tipoMoneda"] = self.currency_id.name

        # ——————————————————————
        # Ajustes finales según tipoOperacion
        if invoice_info["tipoOperacion"] == 1:
            invoice_info["tipoModelo"]       = 1
            invoice_info["tipoContingencia"] = None
            invoice_info["motivoContin"]     = None
        else:
            invoice_info["tipoModelo"] = 2
            if invoice_info["tipoContingencia"] != 5:
                invoice_info["motivoContin"] = None

        # ——————————————————————
        # Log final de todo el payload de identificación
        try:
            _logger.info(
                "SIT CCF Identificación — payload final:\n%s",
                json.dumps(invoice_info, indent=2, ensure_ascii=False),
            )
        except Exception as e:
            _logger.error("SIT Error al serializar payload final: %s", e)

        return invoice_info

    def sit__ccf_base_map_invoice_info_documentoRelacionado(self):
        invoice_info = {}
        return invoice_info

    def sit__ccf_base_map_invoice_info_emisor(self):
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
        direccion["departamento"] =  self.company_id.state_id.code
        direccion["municipio"] =  self.company_id.munic_id.code
        direccion["complemento"] =  self.company_id.street
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

    def sit__ccf_base_map_invoice_info_receptor(self):
        _logger.info("SIT sit_base_map_invoice_info_receptor self = %s", self)
        direccion_rec = {}
        invoice_info = {}
        nit = self.partner_id.fax
        _logger.info("SIT Documento receptor = %s", self.partner_id.dui)
        if isinstance(nit, str):
            nit = nit.replace("-", "")
            invoice_info["nit"] = nit
        nrc = self.partner_id.nrc
        if isinstance(nrc, str):
            nrc = nrc.replace("-", "")
        invoice_info["nrc"] = nrc
        invoice_info["nombre"] = self.partner_id.name
        invoice_info["codActividad"] = self.partner_id.codActividad.codigo
        invoice_info["descActividad"] = self.partner_id.codActividad.valores
        if  self.partner_id.nombreComercial:
            invoice_info["nombreComercial"] = self.partner_id.nombreComercial
        else:
            invoice_info["nombreComercial"] = None
        if self.partner_id.state_id.code: 
            direccion_rec["departamento"] =  self.partner_id.state_id.code
        else:
             direccion_rec["departamento"] =  None
        if self.partner_id.munic_id.code: 
            direccion_rec["municipio"] =  self.partner_id.munic_id.code
        else:
             direccion_rec["municicipio"] =  None 
        if self.partner_id.street: 
            direccion_rec["complemento"] =  self.partner_id.street
        else:
             direccion_rec["complemento"] =  None          
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

    def sit_ccf_base_map_invoice_info_cuerpo_documento(self):
        lines = []
        item_numItem = 0
        total_Gravada = 0.0
        totalIva = 0.0
        codigo_tributo = None  # ← Asegura que siempre esté inicializada

        for line in self.invoice_line_ids.filtered(lambda x: x.price_unit > 0):
            item_numItem += 1
            line_temp = {}
            lines_tributes = []
            line_temp["numItem"] = item_numItem
            tipoItem = int(line.product_id.tipoItem.codigo or line.product_id.product_tmpl_id.tipoItem.codigo)
            line_temp["tipoItem"] = tipoItem
            line_temp["numeroDocumento"] = None
            line_temp["codigo"] = line.product_id.default_code
            codTributo = line.product_id.tributos_hacienda_cuerpo.codigo
            line_temp["codTributo"] = codTributo if codTributo else None
            line_temp["descripcion"] = line.name
            line_temp["cantidad"] = line.quantity

            # Validación UOM
            if not line.product_id.uom_hacienda:
                raise UserError(_("UOM de producto no configurado para:  %s" % (line.product_id.name)))
            uniMedida = int(line.product_id.uom_hacienda.codigo)
            line_temp["uniMedida"] = uniMedida

            line_temp["precioUni"] = round(line.price_unit, 4)
            line_temp["montoDescu"] = round(line_temp["cantidad"] * (line.price_unit * (line.discount / 100)) / 1.13,
                                            2) or 0.0
            line_temp["ventaNoSuj"] = 0.0
            line_temp["ventaExenta"] = 0.0

            ventaGravada = round(line_temp["cantidad"] * (line.price_unit - (line.price_unit * (line.discount / 100))),
                                 2)
            line_temp["ventaGravada"] = ventaGravada

            # Calcular tributos
            for line_tributo in line.tax_ids.filtered(lambda x: x.tributos_hacienda):
                codigo_tributo = line_tributo.tributos_hacienda  # ← Se asigna el objeto, no solo el código
                codigo_tributo_codigo = line_tributo.tributos_hacienda.codigo
                lines_tributes.append(codigo_tributo_codigo)

            # Tributos según tipo de item
            if ventaGravada == 0.0:
                line_temp["tributos"] = None
            elif tipoItem == 4:
                line_temp["uniMedida"] = 99
                line_temp["codTributo"] = codTributo
                line_temp["tributos"] = [20]
            else:
                line_temp["codTributo"] = None
                line_temp["tributos"] = lines_tributes

            # Cálculo de IVA
            vat_taxes_amounts = line.tax_ids.compute_all(
                line.price_unit,
                self.currency_id,
                line.quantity,
                product=line.product_id,
                partner=self.partner_id,
            )
            vat_taxes = vat_taxes_amounts.get('taxes', [])
            vat_taxes_amount = vat_taxes[0].get('amount', 0.0) if vat_taxes else 0.13
            sit_amount_base = round(vat_taxes[0].get('base', 0.0), 2) if vat_taxes else 0.13

            line_temp['psv'] = line.product_id.sit_psv
            line_temp["noGravado"] = 0.0

            if line_temp["cantidad"] > 0:
                price_unit = round(sit_amount_base / line_temp["cantidad"], 4)
            else:
                price_unit = 0.00
            line_temp["precioUni"] = price_unit

            ventaGravada = round((sit_amount_base - (line.price_unit * (line.discount / 100))), 2)
            total_Gravada += ventaGravada
            line_temp["ventaGravada"] = ventaGravada

            totalIva += round(
                vat_taxes_amount - ((((line.price_unit * line.quantity) * (line.discount / 100)) / 1.13) * 0.13), 2)

            lines.append(line_temp)
            self.check_parametros_linea_firmado(line_temp)

        return lines, codigo_tributo, total_Gravada, line.tax_ids, totalIva

    def sit_ccf_base_map_invoice_info_resumen(self, total_Gravada, total_tributos, totalIva, identificacion):
        _logger.info("SIT sit_base_map_invoice_info_resumen self = %s", self)
        total_des = 0
        por_des = 0
        for line in self.invoice_line_ids.filtered(lambda x: x.price_unit < 0):
            total_des += (line.price_unit * -1/1.13)
        if total_des:
            total_gral = self.amount_total + (total_des)
            por_des = 100 - round(((total_gral- (total_des*1.13)) / total_gral) * 100) 
        invoice_info = {}
        tributos = {}
        pagos = {}
        invoice_info["totalNoSuj"] = 0
        invoice_info["totalExenta"] = 0
        invoice_info["totalGravada"] = round(total_Gravada, 2 )
        invoice_info["subTotalVentas"] = round(total_Gravada, 2 )
        invoice_info["descuNoSuj"] = 0
        invoice_info["descuExenta"] = 0
        invoice_info["descuGravada"] = round(total_des, 2)
        invoice_info["porcentajeDescuento"] = por_des
        invoice_info["totalDescu"] = 0
        _logger.info("SIT  identificacion[tipoDte] = %s", identificacion['tipoDte'] )
        _logger.info("SIT  identificacion[tipoDte] = %s", identificacion )
        _logger.info("SIT resumen totalIVA ========================== %s", totalIva)
        tributos["codigo"] = total_tributos.tributos_hacienda.codigo
        tributos["descripcion"] = total_tributos.tributos_hacienda.valores
        tributos["valor"] =  round(totalIva -(total_des*0.13),2) 
        invoice_info["tributos"] = [ tributos ]
        invoice_info["subTotal"] = round(total_Gravada - total_des, 2 )
        invoice_info["ivaPerci1"] = 0
        retencion = 0.0
        #for group in self.tax_totals['groups_by_subtotal'].get('Importe sin impuestos', []):
        groups_by_subtotal = self.tax_totals.get('groups_by_subtotal', {})
        for group in groups_by_subtotal.get('Importe sin impuestos', []):
            if group.get('tax_group_name') == 'Retencion':
                retencion = group.get('tax_group_amount', 0.0)
        retencion = abs(retencion)
        invoice_info["ivaRete1"] = retencion
        invoice_info["reteRenta"] = 0
        invoice_info["montoTotalOperacion"] = round(self.amount_total + retencion, 2 )
        invoice_info["totalNoGravado"] = 0
        invoice_info["totalPagar"] = round(self.amount_total, 2 )
        invoice_info["totalLetras"] = self.amount_text
        invoice_info["saldoFavor"] = 0
        invoice_info["condicionOperacion"] = int(self.condiciones_pago)
        pagos = {}
        pagos["codigo"] = self.forma_pago.codigo
        pagos["montoPago"] = round(self.amount_total, 2)
        pagos["referencia"] = None  

        if int(self.condiciones_pago) in [2]:
            pagos["plazo"] = self.sit_plazo.codigo   
            pagos["periodo"] = self.sit_periodo   
            invoice_info["pagos"] = [pagos]  
        else:
            pagos["plazo"] = None  
            pagos["periodo"] = None     
            invoice_info["pagos"] = [pagos]
            _logger.info("SIT Formas de pago = %s=, %s=", self.forma_pago, pagos)

        invoice_info["numPagoElectronico"] = None
        if invoice_info["totalGravada"] == 0.0:
            invoice_info["ivaPerci1"] = 0.0
            invoice_info["ivaRete1"] = 0.0
        if invoice_info["totalPagar"] == 0.0:
            invoice_info["condicionOperacion"] = 1
        return invoice_info        

    def sit_ccf_base_map_invoice_info_extension(self):
        invoice_info = {}
        invoice_info["nombEntrega"] = self.invoice_user_id.name
        invoice_info["docuEntrega"] = self.company_id.vat
        if  self.partner_id.nombreComercial:
            invoice_info["nombRecibe"] = self.partner_id.nombreComercial
        else:
            invoice_info["nombRecibe"] = None
        nit=self.partner_id.dui
        if isinstance(nit, str):
            nit = nit.replace("-", "")
            invoice_info["docuRecibe"] = nit
        invoice_info["observaciones"] = None
        invoice_info["placaVehiculo"] = None
        return invoice_info


###--------FE-FACTURA ELECTRONICA-----------##

    def sit_base_map_invoice_info(self):
        _logger.info("SIT sit_base_map_invoice_info self = %s", self)
        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        invoice_info["dteJson"] = self.sit_base_map_invoice_info_dtejson()
        return invoice_info

    def sit_base_map_invoice_info_dtejson(self):
        invoice_info = {}
        invoice_info["identificacion"] = self.sit_base_map_invoice_info_identificacion()
        invoice_info["documentoRelacionado"] = None
        invoice_info["emisor"] = self.sit_base_map_invoice_info_emisor()
        invoice_info["receptor"] = self.sit_base_map_invoice_info_receptor()
        invoice_info["otrosDocumentos"] = None
        invoice_info["ventaTercero"] = None
        cuerpoDocumento = self.sit_base_map_invoice_info_cuerpo_documento()
        invoice_info["cuerpoDocumento"] = cuerpoDocumento[0]
        if str(invoice_info["cuerpoDocumento"]) == 'None':
            raise UserError(_('La Factura no tiene linea de Productos Valida.'))        
        invoice_info["resumen"] = self.sit_base_map_invoice_info_resumen(cuerpoDocumento[1], cuerpoDocumento[2], cuerpoDocumento[3],  invoice_info["identificacion"]  )
        invoice_info["extension"] = self.sit_base_map_invoice_info_extension()
        invoice_info["apendice"] = None
        return invoice_info        

    def sit_base_map_invoice_info_identificacion(self):
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
            cod_estable = self.journal_id.cod_sit_estable or '0000MOO1'

            # Obtener la secuencia desde ir.sequence con padding 15
            correlativo = self.env['ir.sequence'].next_by_code('dte.secuencia') or '0'
            correlativo = correlativo.zfill(15)

            # Construir el número de control completo
            invoice_info["numeroControl"] = f"DTE-{tipo_dte}-0000{cod_estable}-{correlativo}"
        else:
            invoice_info["numeroControl"] = self.name
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()
        invoice_info["tipoModelo"] = int(self.sit_modelo_facturacion)
        invoice_info["tipoOperacion"] = int(self.sit_tipo_transmision)
        invoice_info["tipoContingencia"] = None
        invoice_info["motivoContin"] = None

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
            invoice_info["tipoContingencia"] = None
        if invoice_info["tipoContingencia"] == 5:
            invoice_info["motivoContin"] = "Motivo de Contingencia"
        return invoice_info        

    def sit_base_map_invoice_info_emisor(self):
        _logger.info("SIT sit_base_map_invoice_info_emisor self = %s", self)
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
        invoice_info["codEstableMH"] =  None
        invoice_info["codEstable"] =  None
        invoice_info["codPuntoVentaMH"] =  None
        invoice_info["codPuntoVenta"] =  None
        return invoice_info        
    
    def sit_base_map_invoice_info_receptor(self):
        _logger.info("SIT sit_base_map_invoice_info_receptor self = %s", self)
        direccion_rec = {}
        invoice_info = {}
         # Número de Documento (Nit)
        #nit = self.partner_id.vat.replace("-", "") if self.partner_id.vat and isinstance(self.partner_id.vat, str) else None
        nit = self.partner_id.dui.replace("-", "") if self.partner_id.dui and isinstance(self.partner_id.dui, str) else None
        invoice_info["numDocumento"] = nit
        # Establece 'tipoDocumento' como None si 'nit' es None
        tipoDocumento = self.partner_id.l10n_latam_identification_type_id.codigo if self.partner_id.l10n_latam_identification_type_id and nit else None
        invoice_info["tipoDocumento"] = tipoDocumento
        # Número de Registro de Contribuyente (NRC)
        nrc = self.partner_id.nrc.replace("-", "") if self.partner_id.nrc and isinstance(self.partner_id.nrc, str) else None
        invoice_info["nrc"] = nrc
        invoice_info["nombre"] = self.partner_id.name if self.partner_id.name else None
        # Código y Descripción de Actividad
        codActividad = self.partner_id.codActividad.codigo if self.partner_id.codActividad and hasattr(self.partner_id.codActividad, 'codigo') else None
        invoice_info["codActividad"] = codActividad
        descActividad = self.partner_id.codActividad.valores if self.partner_id.codActividad and hasattr(self.partner_id.codActividad, 'valores') else None
        invoice_info["descActividad"] = descActividad
        # Dirección
        direccion_rec["departamento"] = self.partner_id.state_id.code if self.partner_id.state_id and hasattr(self.partner_id.state_id, 'code') else None
        direccion_rec["municipio"] = self.partner_id.munic_id.code if self.partner_id.munic_id and hasattr(self.partner_id.munic_id, 'code') else None
        direccion_rec["complemento"] = self.partner_id.street if self.partner_id.street else None
         # Verifica si alguno de los campos de la dirección es None
        if None in [direccion_rec["departamento"], direccion_rec["municipio"], direccion_rec["complemento"]]:
            invoice_info["direccion"] = None
        else:
            invoice_info["direccion"] = direccion_rec
        # Teléfono y Correo (Requeridos)
        invoice_info["telefono"] = self.partner_id.phone if self.partner_id.phone else None
        invoice_info["correo"] = self.partner_id.email if self.partner_id.email else None
        return invoice_info

    def sit_base_map_invoice_info_cuerpo_documento(self):
        lines = []
        _logger.info("SIT sit_base_map_invoice_info_cuerpo_documento self = %s", self.invoice_line_ids)
        item_numItem = 0
        total_Gravada = 0.0
        totalIva = 0.0
        for line in self.invoice_line_ids.filtered(lambda x: x.price_unit > 0):
            item_numItem += 1       
            line_temp = {}
            lines_tributes = []
            line_temp["numItem"] = item_numItem
            tipoItem = int(line.product_id.tipoItem.codigo or line.product_id.product_tmpl_id.tipoItem.codigo)
            line_temp["tipoItem"] = tipoItem
            line_temp["numeroDocumento"] = None
            line_temp["cantidad"] = line.quantity
            line_temp["codigo"] = line.product_id.default_code
            if not line.product_id:
                _logger.error("Producto no configurado en la línea de factura.")
                continue  # O puedes decidir manejar de otra manera
            product_name = line.product_id.name or "Desconocido"
            if not line.product_id.uom_hacienda:
                raise UserError(_("Unidad de medida del producto no configurada para: %s" % product_name))
            else:
                _logger.info("SIT uniMedida self = %s",  line.product_id)
                _logger.info("SIT uniMedida self = %s",  line.product_id.uom_hacienda)
                uniMedida = int(line.product_id.uom_hacienda.codigo)
            line_temp["uniMedida"] = int(uniMedida)

            line_temp["descripcion"] = line.name
            line_temp["precioUni"] = round(line.price_unit,2)
            line_temp["montoDescu"] = (
                line_temp["cantidad"]  * (line.price_unit * (line.discount / 100))
                or 0.0
            )
            line_temp["ventaNoSuj"] = 0.0
            codigo_tributo = None
            for line_tributo in line.tax_ids:
                codigo_tributo_codigo = line_tributo.tributos_hacienda.codigo
                codigo_tributo = line_tributo.tributos_hacienda
            lines_tributes.append(codigo_tributo_codigo)
            line_temp["tributos"] = lines_tributes
            vat_taxes_amounts = line.tax_ids.compute_all(
                line.price_unit,
                self.currency_id,
                line.quantity,
                product=line.product_id,
                partner=self.partner_id,
            )
            vat_taxes_amount = round( vat_taxes_amounts['taxes'][0]['amount'], 2 )
            sit_amount_base = round( vat_taxes_amounts['taxes'][0]['base'], 2 )
            line_temp['psv'] =  line.product_id.sit_psv
            line_temp["noGravado"] = 0.0 
            line_temp["ivaItem"] = round(vat_taxes_amount - ((((line.price_unit *line.quantity)* (line.discount / 100))/1.13)*0.13),2)
            if line_temp["ivaItem"] == 0.0:
                ventaGravada = 0.0
                ventaExenta = line_temp["cantidad"] * (line.price_unit - (line.price_unit * (line.discount / 100)))
            else:
                ventaGravada = line_temp["cantidad"] * (line.price_unit - (line.price_unit * (line.discount / 100)))
                ventaExenta = 0.0  # O lo que corresponda en caso de que haya IVA
            total_Gravada +=  ventaGravada
            line_temp["ventaGravada"] = round(ventaGravada,2)
            line_temp["ventaExenta"] = round(ventaExenta,2)
            if ventaGravada == 0.0:
                line_temp["tributos"] = None
            if tipoItem == 4:
                line_temp["uniMedida"] = 99
                line_temp["codTributo"] = codTributo
                line_temp["codTributo"] = None    #<------------- Temporal
                line_temp["tributos"] = None
            else:
                line_temp["codTributo"] = None
                line_temp["tributos"] = lines_tributes
                line_temp["tributos"] = None      # <-----   temporal
                line_temp["uniMedida"] = int(uniMedida)
            totalIva += line_temp["ivaItem"]
            lines.append(line_temp)
            self.check_parametros_linea_firmado(line_temp)
        return lines, codigo_tributo, total_Gravada, float(totalIva)

    def sit_base_map_invoice_info_resumen(self, tributo_hacienda, total_Gravada, totalIva, identificacion):
        _logger.info("SIT sit_base_map_invoice_info_resumen self = %s", self)
        total_des = 0
        por_des = 0
        for line in self.invoice_line_ids.filtered(lambda x: x.price_unit < 0):
            total_des += (line.price_unit * -1)
        if total_des:
            total_gral = self.amount_total + total_des
            por_des = 100 - round(((total_gral- total_des) / total_gral) * 100) 
        invoice_info = {}
        tributos = {}
        pagos = {}
        invoice_info["totalNoSuj"] = 0
        invoice_info["totalExenta"] = 0
        invoice_info["subTotalVentas"] = round (self.amount_total + total_des , 2 )
        invoice_info["descuNoSuj"] = 0
        invoice_info["descuExenta"] = 0
        invoice_info["descuGravada"] = round(total_des, 2)
        invoice_info["porcentajeDescuento"] = por_des
        invoice_info["totalDescu"] = 0
        if identificacion['tipoDte'] != "01":
            if  tributo_hacienda:
                _logger.info("SIT tributo_haciendatributo_hacienda = %s", tributo_hacienda)
                tributos["codigo"] = tributo_hacienda.codigo
                tributos["descripcion"] = tributo_hacienda.valores
                tributos["valor"] = round(self.amount_tax, 2 )
            else:
                tributos["codigo"] = None
                tributos["descripcion"] = None
                tributos["valor"] = None
            invoice_info["tributos"] = tributos
        else:
            invoice_info["tributos"] = None
        invoice_info["subTotal"] = round(self.amount_total, 2 )  
        invoice_info["ivaRete1"] = 0
        invoice_info["reteRenta"] = 0
        invoice_info["montoTotalOperacion"] = round(self.amount_total, 2 )
        invoice_info["totalNoGravado"] = 0
        invoice_info["totalPagar"] = round(self.amount_total, 2 )
        invoice_info["totalLetras"] = self.amount_text
        invoice_info["totalIva"] = round(totalIva - (total_des - (total_des / 1.13)), 2 )
        if invoice_info["totalIva"] == 0.0:
            invoice_info["totalGravada"]  = 0.0
            invoice_info["totalExenta"] = round(self.amount_total, 2 )
        else:
            invoice_info["totalGravada"]  = round(self.amount_total + total_des, 2 )
            invoice_info["totalExenta"] = 0.0
        invoice_info["saldoFavor"] = 0
        invoice_info["condicionOperacion"] = int(self.condiciones_pago)
        pagos["codigo"] = self.forma_pago.codigo  
        pagos["montoPago"] = round(self.amount_total, 2 )
        pagos["referencia"] =  self.sit_referencia  
        if int(self.condiciones_pago) in [ 2, 3 ]:
            pagos["periodo"] = self.sit_periodo  
            pagos["plazo"] = self.sit_plazo.codigo   
            invoice_info["pagos"] = [pagos] 
        else:
            pagos["periodo"] = None        
            pagos["plazo"] = None
            invoice_info["pagos"] = None

        if invoice_info["totalGravada"] == 0.0:
            invoice_info["ivaRete1"] = 0.0
        invoice_info["numPagoElectronico"] = None
        return invoice_info        

    def sit_base_map_invoice_info_extension(self):
        invoice_info = {}
        invoice_info["nombEntrega"] = self.invoice_user_id.name
        invoice_info["docuEntrega"] = self.company_id.vat
        invoice_info["nombRecibe"] = self.partner_id.nombreComercial if self.partner_id.nombreComercial else None
        # Asegurarse de que 'nit' sea una cadena antes de usar 'replace'
        nit = self.partner_id.dui if isinstance(self.partner_id.dui, str) else None
        if nit:
            nit = nit.replace("-", "")
        nit = self.partner_id.dui.replace("-", "") if self.partner_id.dui and isinstance(self.partner_id.dui, str) else None
        invoice_info["docuRecibe"] = nit
        invoice_info["observaciones"] = None
        invoice_info["placaVehiculo"] = None
        invoice_info["observaciones"] = None
        invoice_info["placaVehiculo"] = None
        return invoice_info

    def sit_obtener_payload_dte_info(self, ambiente, doc_firmado):
        invoice_info = {}
        invoice_info["ambiente"] = ambiente
        invoice_info["idEnvio"] = "00001"
        invoice_info["tipoDte"] = self.journal_id.sit_tipo_documento.codigo 
        if invoice_info["tipoDte"] == '01':
            invoice_info["version"] = 1
        elif invoice_info["tipoDte"] == '03':
            invoice_info["version"] = 3
        elif invoice_info["tipoDte"] == '05':
            invoice_info["version"] = 3
        elif invoice_info["tipoDte"] == '11':
            invoice_info["version"] = 1
        elif invoice_info["tipoDte"] == '14':
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

    ##################################### NOTA DE CREDITO

    def sit_base_map_invoice_info_ndc(self):
        _logger.info("SIT sit_base_map_invoice_info_ndc self = %s", self)
        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        invoice_info["dteJson"] = self.sit_base_map_invoice_info_ndc_dtejson()
        return invoice_info

    def sit_base_map_invoice_info_ndc_dtejson(self):
        _logger.info("SIT sit_base_map_invoice_info_dtejson self = %s", self)
        invoice_info = {}        
        invoice_info["identificacion"] = self.sit_ndc_base_map_invoice_info_identificacion()
        invoice_info["documentoRelacionado"] = self.sit__ndc_relacionado()
        invoice_info["emisor"] = self.sit__ndc_base_map_invoice_info_emisor()
        invoice_info["receptor"] = self.sit__ccf_base_map_invoice_info_receptor()
        invoice_info["ventaTercero"] = None
        cuerpoDocumento = self.sit_base_map_invoice_info_cuerpo_documento_ndc()
        invoice_info["cuerpoDocumento"] = cuerpoDocumento[0]
        if str(invoice_info["cuerpoDocumento"]) == 'None':
            raise UserError(_('La Factura no tiene linea de Productos Valida.'))        
        invoice_info["resumen"] = self.sit_ndc_base_map_invoice_info_resumen(cuerpoDocumento[1], cuerpoDocumento[2], cuerpoDocumento[3],  invoice_info["identificacion"]  )
        invoice_info["extension"] = self.sit_base_map_invoice_info_extension_ndc()
        invoice_info["apendice"] = None
        return invoice_info 

    def sit_ndc_base_map_invoice_info_identificacion(self):
        invoice_info = {}
        invoice_info["version"] = 3
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
            cod_estable = self.journal_id.cod_sit_estable or '0000MOO1'

            # Obtener la secuencia desde ir.sequence con padding 15
            correlativo = self.env['ir.sequence'].next_by_code('dte.secuencia') or '0'
            correlativo = correlativo.zfill(15)

            # Construir el número de control completo
            invoice_info["numeroControl"] = f"DTE-{tipo_dte}-0000{cod_estable}-{correlativo}"
        else:
            invoice_info["numeroControl"] = self.name
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()          #  company_id.sit_uuid.upper()
        invoice_info["tipoModelo"] = int(self.sit_modelo_facturacion)
        invoice_info["tipoOperacion"] = int(self.sit_tipo_transmision)
        tipoContingencia = int(self.sit_tipo_contingencia)
        invoice_info["tipoContingencia"] = tipoContingencia
        motivoContin = str(self.sit_tipo_contingencia_otro)
        invoice_info["motivoContin"] = motivoContin
        import datetime
        if self.fecha_facturacion_hacienda:
            FechaEmi = self.fecha_facturacion_hacienda
        else:
            FechaEmi = datetime.datetime.now()
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
        return invoice_info        

    def sit_base_map_invoice_info_cuerpo_documento_ndc(self):
        lines = []
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
            if self.inv_refund_id:
                line_temp["numeroDocumento"] = self.inv_refund_id.hacienda_codigoGeneracion_identificacion
            else:
                line_temp["numeroDocumento"] = None 
            line_temp["codigo"] = line.product_id.default_code
            codTributo = line.product_id.tributos_hacienda_cuerpo.codigo
            if codTributo == False:
                line_temp["codTributo"] = None
            else:
                line_temp["codTributo"] = line.product_id.tributos_hacienda_cuerpo.codigo
            line_temp["descripcion"] = line.name
            line_temp["cantidad"] = line.quantity
            if not line.product_id.uom_hacienda:
                uniMedida = 7
                raise UserError(_("UOM de producto no configurado para:  %s" % (line.product_id.name)))
            else:
                uniMedida = int(line.product_id.uom_hacienda.codigo)
            line_temp["uniMedida"] = int(uniMedida)
            line_temp["precioUni"] = round(line.price_unit, 4)
            line_temp["montoDescu"] = (
                round(line_temp["cantidad"]  * (line.price_unit * (line.discount / 100)),2)or 0.0)         
            line_temp["ventaNoSuj"] = 0.0 
            line_temp["ventaExenta"] = 0.0
            ventaGravada = line_temp["cantidad"]  * (line.price_unit * (line.discount / 100))
            line_temp["ventaGravada"] = round(ventaGravada, 2)
            for line_tributo in line.tax_ids:
                codigo_tributo_codigo = line_tributo.tributos_hacienda.codigo
                codigo_tributo = line_tributo.tributos_hacienda
            lines_tributes.append(codigo_tributo_codigo)
            line_temp["tributos"] = lines_tributes
            vat_taxes_amounts = line.tax_ids.compute_all(
                line.price_unit,
                self.currency_id,
                line.quantity,
                product=line.product_id,
                partner=self.partner_id,
            )
            vat_taxes_amount =  vat_taxes_amounts['taxes'][0]['amount']
            sit_amount_base = round( vat_taxes_amounts['taxes'][0]['base'], 2 )
            price_unit_mas_iva = round(line.price_unit, 4)
            if line_temp["cantidad"] > 0:
                price_unit = round(sit_amount_base / line_temp["cantidad"], 4)
            else:
                price_unit = round(0.00, 4)
            line_temp["precioUni"] = price_unit
            ventaGravada =  line_temp["cantidad"]  * line_temp["precioUni"] -   line_temp["montoDescu"]
            total_Gravada +=  round(ventaGravada,4)
            line_temp["ventaGravada"] = round(ventaGravada, 4)
            if ventaGravada == 0.0:
                line_temp["tributos"] = None
            else:
                line_temp["tributos"] = lines_tributes
            if tipoItem == 4:
                line_temp["uniMedida"] = 99
                line_temp["codTributo"] = codTributo
                line_temp["tributos"] = [ 20 ]
            else:
                line_temp["codTributo"] = None
                line_temp["tributos"] = lines_tributes
            totalIva += vat_taxes_amount
            lines.append(line_temp)
            self.check_parametros_linea_firmado(line_temp)
        return lines, codigo_tributo, total_Gravada, line.tax_ids, totalIva

    def sit_ndc_base_map_invoice_info_resumen(self, tributo_hacienda, total_Gravada, totalIva, identificacion):
        invoice_info = {}
        tributos = {}
        pagos = {}
        invoice_info["totalNoSuj"] = 0
        invoice_info["totalExenta"] = 0
        invoice_info["totalGravada"] = round(total_Gravada, 2 )
        invoice_info["subTotalVentas"] = round (total_Gravada , 2 )
        invoice_info["descuNoSuj"] = 0
        invoice_info["descuExenta"] = 0
        invoice_info["descuGravada"] = 0
        invoice_info["totalDescu"] = 0
        if identificacion['tipoDte'] != "01":
            if tributo_hacienda:
                tributos["codigo"] = tributo_hacienda.codigo
                tributos["descripcion"] = tributo_hacienda.valores
                tributos["valor"] = round(self.amount_tax, 2 )
            else:
                tributos["codigo"] = None
                tributos["descripcion"] = None
                tributos["valor"] = None
            _logger.info("========================AÑADIENDO TRIBUTO======================")
            invoice_info["tributos"] = [tributos]
        else:
            invoice_info["tributos"] = None
        invoice_info["subTotal"] = round(total_Gravada, 2 )             #     self.             amount_untaxed
        invoice_info["ivaPerci1"] = 0.0
        invoice_info["ivaRete1"] = 0
        invoice_info["reteRenta"] = 0
        invoice_info["montoTotalOperacion"] = round(self.amount_total, 2 )        
        invoice_info["totalLetras"] = self.amount_text
        invoice_info["condicionOperacion"] = int(self.condiciones_pago)
        pagos["codigo"] = self.forma_pago.codigo  # '01'   # CAT-017 Forma de Pago    01 = bienes
        pagos["montoPago"] = round(self.amount_total, 2 )
        pagos["referencia"] =  self.sit_referencia   # Un campo de texto llamado Referencia de pago
        if invoice_info["totalGravada"] == 0.0:
            invoice_info["ivaPerci1"] = 0.0
            invoice_info["ivaRete1"] = 0.0
        return invoice_info        

    def sit__ndc_base_map_invoice_info_emisor(self):
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
        direccion["departamento"] =  self.company_id.state_id.code
        direccion["municipio"] =  self.company_id.munic_id.code
        direccion["complemento"] =  self.company_id.street
        invoice_info["direccion"] = direccion
        if  self.company_id.phone:
            invoice_info["telefono"] =  self.company_id.phone
        else:
            invoice_info["telefono"] =  None
        invoice_info["correo"] =  self.company_id.email
        return invoice_info   

    def sit_base_map_invoice_info_extension_ndc(self):
        invoice_info = {}
        invoice_info["nombEntrega"] = self.invoice_user_id.name
        invoice_info["docuEntrega"] = self.company_id.vat
        invoice_info["nombRecibe"] = self.partner_id.nombreComercial if self.partner_id.nombreComercial else None
        # Asegurarse de que 'nit' sea una cadena antes de usar 'replace'
        nit = self.partner_id.dui if isinstance(self.partner_id.dui, str) else None
        if nit:
            nit = nit.replace("-", "")
        nit = self.partner_id.dui.replace("-", "") if self.partner_id.dui and isinstance(self.partner_id.dui, str) else None
        invoice_info["docuRecibe"] = nit
        invoice_info["observaciones"] = None
        invoice_info["observaciones"] = None
        return invoice_info

    def sit__ndc_relacionado(self):
        lines = []
        lines_temp = {}
        lines_temp['tipoDocumento'] = '03'
        lines_temp['tipoGeneracion'] = 2
        lines_temp['numeroDocumento'] = self.inv_refund_id.hacienda_codigoGeneracion_identificacion
        from datetime import timedelta
        invoice_date = self.inv_refund_id.invoice_date
        if invoice_date:
            new_date = invoice_date + timedelta(hours=20)
        lines_temp['fechaEmision'] = self.inv_refund_id.invoice_date
        lines.append(lines_temp)
        return lines