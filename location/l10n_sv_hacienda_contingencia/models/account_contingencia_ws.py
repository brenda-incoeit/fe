##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import pyqrcode

import pytz


import logging

_logger = logging.getLogger(__name__)

tz_el_salvador = pytz.timezone('America/El_Salvador')


class sit_AccountContingencia(models.Model):
    _inherit = "account.contingencia1"

######################################################################################################### FCE-CONTINGENCIA
    def sit__contingencia_base_map_invoice_info(self):
        _logger.info("SIT CONTINGENCIA sit__contingencia_base_map_invoice_info self = %s", self)

        invoice_info = {}
        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["activo"] = True
        invoice_info["passwordPri"] = self.company_id.sit_passwordPri
        _logger.info("SIT sit__contingencia_base_map_invoice_info = %s", invoice_info)

        invoice_info["dteJson"] = self.sit__contingencia_base_map_invoice_info_dtejson()
        return invoice_info

    def sit__contingencia_base_map_invoice_info_dtejson(self):
        _logger.info("SIT sit__contingencia_base_map_invoice_info_dtejson self = %s", self)
        invoice_info = {}
        # self = data_inicial
        
        invoice_info["identificacion"] = self.sit__contingencia__base_map_invoice_info_identificacion()

        invoice_info["emisor"] = self.sit__contingencia__base_map_invoice_info_emisor()

        detalleDTE = self.sit_contingencia_base_map_invoice_info_detalle_DTE()
        _logger.info("SIT Cuerpo documento =%s", detalleDTE)


        invoice_info["detalleDTE"] = detalleDTE
        # if str(invoice_info["cuerpoDocumento"]) == 'None':
            # raise UserError(_('La Factura no tiene linea de Productos Valida.'))        
        invoice_info["motivo"] = self.sit_contingencia__base_map_invoice_info_motivo()
        return invoice_info    

    def sit__contingencia__base_map_invoice_info_identificacion(self):
        _logger.info("SIT sit_base_map_invoice_info_identificacion self = %s", self)
        invoice_info = {}
        # self = data_inicial
        invoice_info["version"] = 3
        validation_type = self._compute_validation_type_2()
        if validation_type == 'homologation': 
            ambiente = "00"
        else:
            ambiente = "01"        
        invoice_info["ambiente"] = ambiente

        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()          #  company_id.sit_uuid.upper()

        import datetime
        import pytz
        if self.fechaHoraTransmision:
            FechaEmi = self.fechaHoraTransmision
        else:
            FechaEmi = datetime.datetime.now()
            FechaEmi = FechaEmi.astimezone(tz_el_salvador)

        _logger.info("SIT FechaEmi = %s (%s)", FechaEmi, type(FechaEmi))
        invoice_info["fTransmision"] = FechaEmi.strftime('%Y-%m-%d')
        invoice_info["hTransmision"] = FechaEmi.strftime('%H:%M:%S')
        _logger.info("SIT  sit__contingencia__base_map_invoice_info_identificacion = %s", invoice_info)
        return invoice_info        

    def sit__contingencia__base_map_invoice_info_emisor(self):
        _logger.info("SIT sit__contingencia__base_map_invoice_info_emisor self = %s", self)

        invoice_info = {}
        direccion = {}

        nit=self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        nrc= self.company_id.company_registry
        invoice_info["nombre"] = self.company_id.name
        invoice_info["nombreResponsable"] = self.company_id.partner_id.user_id.partner_id.name
        invoice_info["tipoDocResponsable"] = "13"
        invoice_info["numeroDocResponsable"] = self.company_id.partner_id.user_id.partner_id.dui
        invoice_info["tipoEstablecimiento"] =  self.company_id.tipoEstablecimiento.codigo
        invoice_info["codEstableMH"] =  None
        invoice_info["codPuntoVenta"] =  None


        if  self.company_id.phone:
            invoice_info["telefono"] =  self.company_id.phone
        else:
            invoice_info["telefono"] =  None

        invoice_info["correo"] =  self.company_id.email
        
        return invoice_info   

    def sit_contingencia_base_map_invoice_info_detalle_DTE(self):
        _logger.info("SIT sit_contingencia_base_map_invoice_info_detalle_DTE self ------------------------- = (%s)  %s", self, self.sit_facturas_relacionadas)
        lines = []


        item_numItem = 0

        for line in self.sit_facturas_relacionadas:     
            item_numItem += 1       
            line_temp = {}
            lines_tributes = []
            line_temp["noItem"] = item_numItem
            codigoGeneracion =  line.hacienda_codigoGeneracion_identificacion
            if not codigoGeneracion:
                MENSAJE = "La Factura " + line.name + " no tiene código de Generacion"
                raise UserError(_(MENSAJE))        
            line_temp["codigoGeneracion"] = line.hacienda_codigoGeneracion_identificacion
            tipoDoc = str(line.journal_id.sit_tipo_documento.codigo)
            line_temp["tipoDoc"] = tipoDoc
            lines.append(line_temp)

        return lines

    def sit_contingencia__base_map_invoice_info_motivo(self):
        _logger.info("SIT sit_contingencia__base_map_invoice_info_motivo self = %s", self)

        invoice_info = {}
        tributos = {}
        pagos = {}


        import datetime
        import pytz

        FechaEmi = self.sit_fInicio_hInicio
        FechaEmi = FechaEmi.astimezone(tz_el_salvador)

        _logger.info("SIT FechaEmi = %s (%s)", FechaEmi, type(FechaEmi))
        FechaFin = self.sit_fFin_hFin
        FechaFin = FechaFin.astimezone(tz_el_salvador)

        _logger.info("SIT FechaEmi = %s (%s)", FechaEmi, type(FechaEmi))


        invoice_info["fInicio"] = FechaEmi.strftime('%Y-%m-%d')
        invoice_info["fFin"] = FechaFin.strftime('%Y-%m-%d')
        invoice_info["hInicio"] = FechaEmi.strftime('%H:%M:%S')
        invoice_info["hFin"] = FechaFin.strftime('%H:%M:%S')

        invoice_info["tipoContingencia"] = int(self.sit_tipo_contingencia.codigo)
        if self.sit_tipo_contingencia_otro:
            motivoContingencia = self.sit_tipo_contingencia_otro
        else:
            motivoContingencia = None

        invoice_info["motivoContingencia"] = motivoContingencia

        return invoice_info      
    

    def sit_obtener_payload_contingencia_dte_info(self, documento):
        invoice_info = {}
        nit = self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["documento"] = documento
        return invoice_info        


    def sit_generar_uuid(self):
        import uuid
        # Genera un UUID versión 4 (basado en números aleatorios)
        uuid_aleatorio = uuid.uuid4()
        uuid_cadena = str(uuid_aleatorio)
        return uuid_cadena.upper()

