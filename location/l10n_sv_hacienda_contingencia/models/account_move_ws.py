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


import datetime
import pytz

# Definir la zona horaria de El Salvador
tz_el_salvador = pytz.timezone('America/El_Salvador')




_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"
















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
        if self.fecha_facturacion_hacienda:
            FechaEmi = self.fecha_facturacion_hacienda
        else:
            FechaEmi = datetime.datetime.now()
        _logger.info("SIT FechaEmi = %s (%s)", FechaEmi, type(FechaEmi))

        invoice_info["fTransmision"] = FechaEmi.strftime('%Y-%m-%d')
        invoice_info["hTransmision"] = FechaEmi.strftime('%H:%M:%S')

        _logger.info("SIT sit_ccf_ base_map_invoice_info_identificacion1 = %s", invoice_info)
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
        _logger.info("SIT sit_contingencia_base_map_invoice_info_detalle_DTE self = %s", self)
        lines = []
        _logger.info("SIT sit_base_map_invoice_info_cuerpo_documento self = %s", self.invoice_line_ids)

        # for line in self.invoice_line_ids.filtered(lambda x: not x.display_type):
        item_numItem = 0

        for line in self:     
            item_numItem += 1       
            line_temp = {}
            lines_tributes = []
            line_temp["noItem"] = item_numItem
            line_temp["codigoGeneracion"] = self.sit_generar_uuid()  

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
        if self.fecha_facturacion_hacienda:
            FechaEmi = self.fecha_facturacion_hacienda
        else:
            FechaEmi = datetime.datetime.now()
        _logger.info("SIT FechaEmi = %s (%s)", FechaEmi, type(FechaEmi))


        invoice_info["fInicio"] = FechaEmi.strftime('%Y-%m-%d')
        invoice_info["fFin"] = FechaEmi.strftime('%Y-%m-%d')
        invoice_info["hInicio"] = FechaEmi.strftime('%H:%M:%S')
        invoice_info["hFin"] = FechaEmi.strftime('%H:%M:%S')

        invoice_info["tipoContingencia"] = int(self.sit_tipo_contingencia.codigo)
        invoice_info["motivoContingencia"] = self.sit_tipo_contingencia_otro

        return invoice_info      
    








######################################### F-ANULACION

    # def sit_obtener_payload_anulacion_dte_info(self,  ambiente, doc_firmado):

    #     _logger.info("SIT sit_obtener_payload_anulacion_dte_info self = %s", self)


    #     # return invoice_info
            
    #     invoice_info = {}
    #     nit = self.company_id.vat
    #     nit = nit.replace("-", "")
    #     invoice_info["ambiente"] = ambiente
    #     invoice_info["idEnvio"] = "00001"
    #     invoice_info["version"] = 2
    #     invoice_info["documento"] = doc_firmado

    #     return invoice_info      

    def sit_obtener_payload_contingencia_dte_info(self, documento):
        invoice_info = {}
        nit = self.company_id.vat
        nit = nit.replace("-", "")
        invoice_info["nit"] = nit
        invoice_info["documento"] = documento
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
        invoice_info["documento"] = doc_firmado
        invoice_info["codigoGeneracion"] = self.sit_generar_uuid()

        return invoice_info        






        # _logger.info("SIT  Generando DTE")
        # if enviroment_type == 'homologation': 
        #     host = 'https://apitest.dtes.mh.gob.sv' 
        #     ambiente = "00"
        # else:
        #     host = 'https://api.dtes.mh.gob.sv'
        #     ambiente = "01"
        # url = host + '/fesv/recepciondtes'

        # Authorization = self.company_id.sit_token
        # idEnvio = 00001
        # version = 3
        # tipoDte = self.l10n_latam_document_type_id.code
        # documento = doc_firmado

        # payload = 'user=06140902221032&pwd=D%237k9r%402mP1!b'
        # headers = {
        # 'Content-Type': 'application/x-www-form-urlencoded'
        # }

        # response = requests.request("POST", url, headers=headers, data=payload)

        # print(response.text)


    def sit_generar_uuid(self):
        import uuid
        # Genera un UUID versión 4 (basado en números aleatorios)
        uuid_aleatorio = uuid.uuid4()
        uuid_cadena = str(uuid_aleatorio)
        return uuid_cadena.upper()

