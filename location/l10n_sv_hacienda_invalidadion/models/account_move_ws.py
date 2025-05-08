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

  


######################################### F-ANULACION




    def sit_anulacion_base_map_invoice_info(self):
        _logger.info("SIT sit_anulacion_base_map_invoice_info_dtejson self = %s", self)

        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        _logger.info("SIT sit_base_map_invoice_info = %s", invoice_info)

        invoice_info["dteJson"] = self.sit_anulacion_base_map_invoice_info_dtejson()
        return invoice_info

    def sit_anulacion_base_map_invoice_info_dtejson(self):
        _logger.info("SIT sit_anulacion_base_map_invoice_info_dtejson self = %s", self)
        # _logger.info("SIT sit_base_map_invoice_info_dtejson data_inicial = %s", data_inicial)

        invoice_info = {}
        # self = data_inicial
        
        invoice_info["identificacion"] = self.sit_invalidacion_base_map_invoice_info_identificacion()
        invoice_info["emisor"] = self.sit_invalidacion_base_map_invoice_info_emisor()
        invoice_info["documento"] = self.sit_invalidacion_base_map_invoice_info_documento()
        
        invoice_info["motivo"] = self.sit_invalidacion_base_map_invoice_info_motivo()
        _logger.info("------------------------>SIT MOTIVO =%s",invoice_info["motivo"])

        return invoice_info        

    def sit_invalidacion_base_map_invoice_info_identificacion(self):
        _logger.info("SIT sit_invalidacion_base_map_invoice_info_identificacion self = %s", self)

        invoice_info = {}
        # self = data_inicial
        invoice_info["version"] = 2

        validation_type = self._compute_validation_type_2()
        if validation_type == 'homologation': 
            ambiente = "00"
        else:
            ambiente = "01"        
        invoice_info["ambiente"] = ambiente

        if self.sit_codigoGeneracion_invalidacion:
            invoice_info["codigoGeneracion"] = self.sit_codigoGeneracion_invalidacion
        else:    
            invoice_info["codigoGeneracion"] = self.sit_generar_uuid()          #  company_id.sit_uuid.upper()

        import datetime
        from datetime import timedelta
        if self.sit_fec_hor_Anula:
            FechaHoraAnulacion = self.sit_fec_hor_Anula

        else:
            FechaHoraAnulacion = datetime.datetime.now()-timedelta(hours=6)
        _logger.info("SIT FechaHoraAnulacion = %s (%s)", FechaHoraAnulacion, type(FechaHoraAnulacion))

        invoice_info["fecAnula"] = FechaHoraAnulacion.strftime('%Y-%m-%d')
        invoice_info["horAnula"] = FechaHoraAnulacion.strftime('%H:%M:%S')
        
        return invoice_info        

    def sit_invalidacion_base_map_invoice_info_emisor(self):
        _logger.info("SIT sit_invalidacion_base_map_invoice_info_emisor self = %s", self)

        invoice_info = {}
        direccion = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit

        invoice_info["nombre"] = self.company_id.name

        invoice_info["tipoEstablecimiento"] =  self.company_id.tipoEstablecimiento.codigo
        invoice_info["nomEstablecimiento"] =  self.company_id.tipoEstablecimiento.valores

        # invoice_info["direccion"] = direccion
        invoice_info["codEstableMH"] =  self.journal_id.sit_codestable  # None
        invoice_info["codEstable"] =  self.journal_id.sit_codestable    #  None
        invoice_info["codPuntoVentaMH"] =  self.journal_id.sit_codpuntoventa    # None
        invoice_info["codPuntoVenta"] =  self.journal_id.sit_codpuntoventa    # None
        if  self.company_id.phone:
            invoice_info["telefono"] =  self.company_id.phone
        else:
            invoice_info["telefono"] =  None

        invoice_info["correo"] =  self.company_id.email

        return invoice_info    
       

    def sit_invalidacion_base_map_invoice_info_documento(self):
        _logger.info("SIT sit_invalidacion_base_map_invoice_info_documento self = %s", self)
        invoice_info = {}

        invoice_info["tipoDte"] =  self.journal_id.sit_tipo_documento.codigo
        invoice_info["codigoGeneracion"] = self.hacienda_codigoGeneracion_identificacion
        invoice_info["selloRecibido"] = self.hacienda_selloRecibido
        invoice_info["numeroControl"] = self.name
        import datetime
        from datetime import timedelta 
        # Suponiendo que self.fecha_facturacion_hacienda es una cadena en formato 'YYYY-MM-DD'
        if isinstance(self.fecha_facturacion_hacienda, str):
            fecha_facturacion = datetime.strptime(self.fecha_facturacion_hacienda, '%Y-%m-%d')
        else:
            fecha_facturacion = self.fecha_facturacion_hacienda

        # Restar 6 horas
        adjusted_fecha = fecha_facturacion - timedelta(hours=6)

        # Continuar con el uso de adjusted_fecha
        invoice_info["fecEmi"] = adjusted_fecha.strftime('%Y-%m-%d')
        # invoice_info["montoIva"] = self._compute_total_iva()
        invoice_info["montoIva"] = None
        if self.sit_codigoGeneracionR == False:
            invoice_info["codigoGeneracionR"] = None
        else:
            invoice_info["codigoGeneracionR"] = self.sit_codigoGeneracionR

        nit = self.partner_id.vat

        # Verifica si nit es una cadena no vacía y no un valor booleano
        if isinstance(nit, str) and nit.strip():
            nit = nit.replace("-", "")
        else:
            nit = None


        invoice_info["numDocumento"] = nit
        # Asignar tipoDocumento en función del valor de nit
        if nit:
            if self.partner_id.l10n_latam_identification_type_id:
                tipoDocumento = self.partner_id.l10n_latam_identification_type_id.codigo
            else:
                tipoDocumento = None
        else:
            tipoDocumento = None

        invoice_info["tipoDocumento"] = tipoDocumento

        if  self.partner_id.name:
            invoice_info["nombre"] = self.partner_id.name
        else:
            invoice_info["nombre"] = None

        if self.partner_id.phone:
            invoice_info["telefono"] =  self.partner_id.phone
        else:
            invoice_info["telefono"] = None
        if self.partner_id.email:
            invoice_info["correo"] =  self.partner_id.email
        else:
            invoice_info["correo"] = None    
        

        # tipoDocumento = None
        # invoice_info["tipoDocumento"] = tipoDocumento
        # invoice_info["numDocumento"] = None
        # invoice_info["nombre"] = None
        # invoice_info["telefono"] = None
        # invoice_info["correo"] =  None

        return  invoice_info

    def _compute_total_iva(self):
        for invoice in self:
            lineas = invoice.invoice_line_ids
            _logger.info("SIT _compute_total_iva invoice.lineas=%s", lineas)
            IVA = 0.0

            for linea in lineas:

                vat_taxes_amounts = linea.tax_ids.compute_all(
                    linea.price_unit,
                    self.currency_id,
                    linea.quantity,
                    product=linea.product_id,
                    partner=self.partner_id,
                )
                _logger.info("SIT vat_taxes_ammounts 0=%s", vat_taxes_amounts['taxes'][0])
                _logger.info("SIT vat_taxes_ammounts 1=%s", vat_taxes_amounts['taxes'][0]['amount'])
                _logger.info("SIT sit_amount_base 1=%s", vat_taxes_amounts['taxes'][0]['base'])
                vat_taxes_amount = round( vat_taxes_amounts['taxes'][0]['amount'], 2 )
                IVA_linea =  vat_taxes_amounts['taxes'][0]['amount']

                _logger.info("SIT _compute_total_iva invoice.line=%s-%s-%s-%s", linea.price_unit, linea.price_subtotal, linea.price_total, linea.discount)
                # IVA_linea = linea.price_total -  linea.discount
                IVA += IVA_linea

            # total_iva = sum(tax.amount for tax in invoice.tax_ids if tax.amount_type == 'percent')
            return   round( IVA, 6 )  
    

    def sit_invalidacion_base_map_invoice_info_motivo(self):
        _logger.info("SIT sit_invalidacion_base_map_invoice_info_documento self = %s", self)
        invoice_info = {}
        nit=self.company_id.partner_id.vat
        nit = nit.replace("-", "")

        invoice_info["tipoAnulacion"] = int(self.sit_tipoAnulacion)
        invoice_info["motivoAnulacion"] = self.sit_motivoAnulacion

        # invoice_info["nombreResponsable"] = self.sit_nombreResponsable.name
        # invoice_info["tipDocResponsable"] = self.sit_tipDocResponsable
        # invoice_info["numDocResponsable"] = self.sit_numDocResponsable

        invoice_info["nombreResponsable"] = self.company_id.partner_id.name
        invoice_info["tipDocResponsable"] = "36"
        invoice_info["numDocResponsable"] = nit

        # invoice_info["nombreSolicita"] = self.sit_nombreSolicita.name
        # invoice_info["tipDocSolicita"] = self.sit_tipDocSolicita
        # invoice_info["numDocSolicita"] = self.sit_numDocSolicita

        invoice_info["nombreSolicita"] =  self.company_id.partner_id.name
        invoice_info["tipDocSolicita"] = "36"
        invoice_info["numDocSolicita"] = nit

        if  invoice_info["tipoAnulacion"] == 3:
            invoice_info["motivoAnulacion"] = self.sit_motivoAnulacion
        else:
            invoice_info["motivoAnulacion"] = None
        # _logger.info("------------------------>SIT MOTIVO =%s",invoice_info)
        if invoice_info["motivoAnulacion"] == False:
            invoice_info["motivoAnulacion"] = None
            
        return  invoice_info



######################################### F-ANULACION

    def sit_obtener_payload_anulacion_dte_info(self,  ambiente, doc_firmado):

        _logger.info("SIT sit_obtener_payload_anulacion_dte_info self = %s", self)


        # return invoice_info
            
        invoice_info = {}
        nit = self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["ambiente"] = ambiente
        invoice_info["idEnvio"] = 1
        invoice_info["version"] = 2
        invoice_info["documento"] = doc_firmado

        return invoice_info      

   
   


    def sit_generar_uuid(self):
        import uuid
        # Genera un UUID versión 4 (basado en números aleatorios)
        uuid_aleatorio = uuid.uuid4()
        uuid_cadena = str(uuid_aleatorio)
        return uuid_cadena.upper()

