##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_repr
from odoo.addons.l10n_sv_haciendaws_fe.afip_utils import get_invoice_number_from_response
import base64
import pyqrcode
import qrcode
import os
from PIL import Image
import io


base64.encodestring = base64.encodebytes
import json
import requests

import logging
import sys
import traceback
from datetime import datetime

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

#---------------------------------------------------------------------------------------------
# Exportacion
#---------------------------------------------------------------------------------------------
    # def _post(self, soft=True):
    #     '''validamos que partner cumple los requisitos basados en el tipo
    # de documento de la sequencia del diario selecionado
    # FACTURA ELECTRONICAMENTE
    # '''
    #     for invoice in self:
    #         if invoice.move_type != 'entry':
    #             type_report = invoice.journal_id.type_report
    #             sit_tipo_documento = invoice.journal_id.sit_tipo_documento.codigo
    #             _logger.info("SIT action_post type_report  = %s", type_report)
    #             _logger.info("SIT action_post sit_tipo_documento  = %s", sit_tipo_documento)
    #             validation_type = self._compute_validation_type_2()
    #             _logger.info("SIT action_post validation_type = %s", validation_type)

    #             # if type_report == 'exp':
    #             #     for l in invoice.invoice_line_ids:
    #             #         if not l.product_id.arancel_id:
    #             #             invoice.msg_error("Posicion Arancelaria del Producto %s" % l.product_id.name)
    #             ambiente = "00"
    #             if validation_type == 'homologacioin':
    #                 ambiente = "00"
    #                 _logger.info("SIT Factura de Prueba")
    #             elif validation_type == 'production':
    #                 _logger.info("SIT Factura de Producción")
    #                 ambiente = "01"
    #             # Firmado de documento
    #             print("FIRMAAAAAAAAAAAAAAAAAAAAA")
    #             print(validation_type)
    #             payload = invoice.obtener_payload_fex(validation_type, sit_tipo_documento)
    #             documento_firmado = ""
    #             payload_original = payload
    #             _logger.info("SIT payload_original = %s ", str((payload_original)) ) 


    #             documento_firmado = invoice.firmar_documento_fex(validation_type, payload)
    #             if documento_firmado:
    #                 _logger.info("SIT Firmado de documento")
    #                 _logger.info("SIT Generando DTE")
    #                 #Obtiene el payload DTE
    #                 payload_dte = invoice.sit_obtener_payload_fex_dte_info(ambiente, documento_firmado)
    #                 self.check_parametros_dte_fex(payload_dte)
    #                 Resultado = invoice.generar_dte_fex(validation_type, payload_dte, payload_original)
    #                 from datetime import datetime, timedelta
    #                 if Resultado:
    #                     dat_time  = Resultado['fhProcesamiento']
    #                     _logger.info("SIT Fecha de procesamiento (%s)%s", type(dat_time), dat_time)
    #                     fhProcesamiento = datetime.strptime(dat_time, '%d/%m/%Y %H:%M:%S')
    #                     _logger.info("SIT Fecha de procesamiento (%s)%s", type(fhProcesamiento), fhProcesamiento)
    #                     MENSAJE="SIT Respuesta = " + str(Resultado)
    #                     invoice.hacienda_estado = Resultado['estado']
    #                     invoice.hacienda_codigoGeneracion_identificacion = Resultado['codigoGeneracion']
    #                     invoice.hacienda_selloRecibido = Resultado['selloRecibido']
    #                     invoice.fecha_facturacion_hacienda = fhProcesamiento + timedelta(hours=6)       #  Resultado['fhProcesamiento']
    #                     invoice.hacienda_clasificaMsg = Resultado['clasificaMsg']
    #                     invoice.hacienda_codigoMsg = Resultado['codigoMsg']
    #                     invoice.hacienda_descripcionMsg = Resultado['descripcionMsg']
    #                     invoice.hacienda_observaciones = str(Resultado['observaciones'])
    #                     codigo_qr = invoice._generar_qr(ambiente, Resultado['codigoGeneracion'], invoice.fecha_facturacion_hacienda )
    #                     invoice.sit_qr_hacienda = codigo_qr
    #                     _logger.info("SIT Factura creada correctamente =%s", MENSAJE)
    #                     _logger.info("SIT Factura creada correctamente state =%s", invoice.state)
    #                     payload_original['dteJson']['firmaElectronica'] = documento_firmado
    #                     payload_original['dteJson']['selloRecibido'] = Resultado['selloRecibido']
    #                     _logger.info("SIT Factura creada correctamente payload_original =%s",   str(json.dumps(payload_original)))  
    #                     invoice.sit_json_respuesta = str(json.dumps(payload_original['dteJson']))
    #                     json_str = json.dumps(payload_original['dteJson'])
    #                     json_base64 = base64.b64encode(json_str.encode('utf-8'))
    #                     file_name = payload_original["dteJson"]["identificacion"]["numeroControl"] + '.json'
    #                     _logger.info("SIT file_name =%s", file_name)
    #                     _logger.info("SIT self._name =%s", self._name)
    #                     _logger.info("SIT invoice.id =%s", invoice.id)
    #                     invoice.env['ir.attachment'].sudo().create(
    #                         {
    #                             'name': file_name,
    #                             'datas': json_base64,
    #                             'res_model': self._name,
    #                             'res_id': invoice.id,
    #                             'mimetype': 'application/json'
    #                         }) 
    #                     _logger.info("SIT json creado........................")
    #                     invoice.state = "draft"
    #                     _logger.critical("Numero de Control")
    #                     _logger.critical(invoice.name)
    #                     return super(AccountMove, self)._post()
    #             else:
    #                 _logger.info("SIT  Documento no firmado")    
    #                 raise UserError(_('SIT Documento NO Firmado'))

    #     return super(AccountMove, self)._post()

    # # FIMAR FIMAR FIRMAR =====================================================================================================    
    # def firmar_documento_fex(self, enviroment_type, payload):
    #     _logger.info("SIT  Firmando de documento")
    #     _logger.info("SIT Documento a FIRMAR =%s", payload)
    #     if enviroment_type == 'homologation': 
    #         ambiente = "00"
    #     else:
    #         ambiente = "01"
    #     host = 'http://svfe-api-firmador:8113'
    #     url = host + '/firmardocumento/'
    #     headers = {'Content-Type': 'application/json'}
    #     try:
    #         MENSAJE = "SIT POST, " + str(url) + ", headers=" + str(headers) + ", data=" + str(json.dumps(payload))
    #         _logger.info("SIT A FIRMAR = %s", MENSAJE)
    #         response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    #     except Exception as e:
    #         error = str(e)
    #         _logger.info('SIT error= %s, ', error)       
    #         if "error" in error or "" in error:
    #             MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) +", " +  str(error['message'])  
    #             raise UserError(_(MENSAJE_ERROR))
    #         else:
    #             raise UserError(_(error))
    #     resultado = []    
    #     json_response = response.json()
    #     if json_response['status'] in [  400, 401, 402 ] :
    #         _logger.info("SIT Error 40X  =%s", json_response['status'])
    #         status=json_response['status']
    #         error=json_response['error']
    #         message=json_response['message']
    #         MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) +", Detalle:" +  str(message)  
    #         raise UserError(_(MENSAJE_ERROR))
    #     if json_response['status'] in [ 'ERROR', 401, 402 ] :
    #         _logger.info("SIT Error 40X  =%s", json_response['status'])
    #         status=json_response['status']
    #         body=json_response['body']
    #         codigo=body['codigo']
    #         message=body['mensaje']
    #         resultado.append(status)
    #         resultado.append(codigo)
    #         resultado.append(message)
    #         MENSAJE_ERROR = "Código de Error:" + str(status) + ", Codigo:" + str(codigo) +", Detalle:" +  str(message)  
    #         raise UserError(_(MENSAJE_ERROR))        
    #     elif json_response['status'] == 'OK':
    #         status=json_response['status']
    #         body=json_response['body']
    #         resultado.append(status)
    #         resultado.append(body)
    #         return body

    def obtener_payload_fex(self, enviroment_type, sit_tipo_documento):
        _logger.info("SIT  Obteniendo payload")
        if enviroment_type == 'homologation': 
            ambiente = "00"
        else:
            ambiente = "01"
        invoice_info = self.sit_fex_base_map_invoice_info()
        _logger.info("SIT invoice_info FExportacion= %s", invoice_info)
        self.check_parametros_firmado_fex()
        _logger.info("SIT payload_data =%s", invoice_info)
        return invoice_info
    

    def generar_dte_fex(self, enviroment_type, payload, payload_original):
        _logger.info("SIT  Generando DTE")
        if enviroment_type == 'homologation': 
            host = 'https://apitest.dtes.mh.gob.sv' 
        else:
            host = 'https://api.dtes.mh.gob.sv'
        url = host + '/fesv/recepciondte'

        if not self.company_id.sit_token_fecha:
            self.company_id.get_generar_token()
        elif self.company_id.sit_token_fecha.date() and  self.company_id.sit_token_fecha.date() < self.date:
            self.company_id.get_generar_token()
        agente = self.company_id.sit_token_user
        authorization = self.company_id.sit_token
        headers = {
         'Content-Type': 'application/json', 
         'User-Agent': agente,
         'Authorization': authorization
        }
        if 'version' not in payload:
            # Si no existe, añadirlo con el valor 3
            payload['version'] = 3
        _logger.info("SIT = requests.request(POST, %s, headers=%s, data=%s)", url, headers, payload)
        try:
            _logger.info("________________________________________________ =%s", payload)
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            _logger.info("SIT DTE response =%s", response)
            _logger.info("SIT DTE response =%s", response.status_code)
            _logger.info("SIT DTE response.text =%s", response.text)
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)       
            if "error" in error or "" in error:
                MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) +", " +  str(error['message'])  
                raise UserError(_(MENSAJE_ERROR))
            else:
                raise UserError(_(error))
        resultado = []    
        _logger.info("SIT DTE decodificando respuestas")
        if response.status_code in [  401 ] :
            MENSAJE_ERROR = "ERROR de conexión : " + str(response )   
            raise UserError(_(MENSAJE_ERROR))
        json_response = response.json()
        _logger.info("SIT json_responset =%s", json_response)
        if json_response['estado'] in [  "RECHAZADO", 402 ] :
            status=json_response['estado']
            ambiente=json_response['ambiente']
            if json_response['ambiente'] == '00':
                ambiente = 'TEST'
            else:
                ambiente = 'PROD'
            clasificaMsg=json_response['clasificaMsg']
            message=json_response['descripcionMsg']
            observaciones=json_response['observaciones']
            MENSAJE_ERROR = "Código de Error..:" + str(status) + ", Ambiente:" + ambiente + ", ClasificaciónMsje:" + str(clasificaMsg) +", Descripcion:" + str(message) +", Detalle:" +  str(observaciones) +", DATA:  " +  str(json.dumps(payload_original))  
            self.hacienda_estado= status
            raise UserError(_(MENSAJE_ERROR))
        status = json_response.get('status')
        if status and status in [400, 401, 402]:
            _logger.info("SIT Error 40X  =%s", status)
            error = json_response.get('error', 'Error desconocido')  # Si 'error' no existe, devuelve 'Error desconocido'
            message = json_response.get('message', 'Mensaje no proporcionado')  # Si 'message' no existe, devuelve 'Mensaje no proporcionado'
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) + ", Detalle:" + str(message)
            raise UserError(_(MENSAJE_ERROR))
        if json_response['estado'] in [  "PROCESADO" ] :
            return json_response
    

    def check_parametros_fex(self):
        if not self.name:
             raise UserError(_('El Número de control no definido'))       
        if not self.company_id.tipoEstablecimiento.codigo:
            raise UserError(_('El tipoEstablecimiento no definido'))        
        if not self.sit_tipoAnulacion or self.sit_tipoAnulacion == False:
            raise UserError(_('El tipoAnulacion no definido'))        

    def check_parametros_firmado_fex(self):
        if not self.journal_id.sit_tipo_documento.codigo:
            raise UserError(_('El Tipo de  DTE no definido.'))
        if not self.name:
            raise UserError(_('El Número de control no definido'))
        if not self.company_id.sit_passwordPri:
            raise UserError(_('El valor passwordPri no definido'))
        if not self.company_id.sit_uuid:
            raise UserError(_('El valor uuid no definido'))
        if not self.company_id.vat:
            raise UserError(_('El emisor no tiene NIT configurado.'))
        if not self.company_id.company_registry:
            raise UserError(_('El emisor no tiene NRC configurado.'))
        if not self.company_id.name:
            raise UserError(_('El emisor no tiene NOMBRE configurado.'))
        if not self.company_id.codActividad:
            raise UserError(_('El emisor no tiene CODIGO DE ACTIVIDAD configurado.'))
        if not self.company_id.tipoEstablecimiento:
            raise UserError(_('El emisor no tiene TIPO DE ESTABLECIMIENTO configurado.'))
        if not self.company_id.state_id:
            raise UserError(_('El emisor no tiene DEPARTAMENTO configurado.'))
        if not self.company_id.munic_id:
            raise UserError(_('El emisor no tiene MUNICIPIO configurado.'))
        if not self.company_id.email:
            raise UserError(_('El emisor no tiene CORREO configurado.'))
        if not self.journal_id.sit_tipo_documento.codigo:
            raise UserError(_('El Tipo de DTE no definido.'))
        if not self.name:
            raise UserError(_('El Número de control no definido'))
        tipo_dte = self.journal_id.sit_tipo_documento.codigo
        if tipo_dte == '11':
            # Solo validar el nombre para DTE tipo 01
            if not self.partner_id.name:
                raise UserError(_('El receptor no tiene NOMBRE configurado para facturas tipo 01.'))
            if not self.partner_id.vat and self.partner_id.is_company:
                _logger.info("SIT, es compañia se requiere NIT")
                raise UserError(_('El receptor no tiene NIT configurado.'))
            if not self.partner_id.nrc and self.partner_id.is_company:
                _logger.info("SIT, es compañia se requiere NRC")
                raise UserError(_('El receptor no tiene NRC configurado.'))
            if not self.partner_id.name:
                raise UserError(_('El receptor no tiene NOMBRE configurado.'))
            if not self.partner_id.codActividad:
                raise UserError(_('El receptor no tiene CODIGO DE ACTIVIDAD configurado.'))
            if not self.partner_id.state_id:
                raise UserError(_('El receptor no tiene DEPARTAMENTO configurado.'))
            if not self.partner_id.munic_id:
                raise UserError(_('El receptor no tiene MUNICIPIO configurado.'))
            if not self.partner_id.email:
                raise UserError(_('El receptor no tiene CORREO configurado.'))

        if not self.invoice_line_ids:
            raise UserError(_('La factura no tiene LINEAS DE PRODUCTOS asociada.'))

    def check_parametros_linea_firmado_fex(self, line_temp):
        if not line_temp["codigo"]:
            ERROR = 'El CODIGO del producto  ' + line_temp["descripcion"] + ' no está definido.'
            raise UserError(_(ERROR))
        if not line_temp["cantidad"]:
            ERROR = 'La CANTIDAD del producto  ' + line_temp["descripcion"] + ' no está definida.'
            raise UserError(_(ERROR))
        if not  line_temp["precioUni"]:
            ERROR = 'El PRECIO UNITARIO del producto  ' + line_temp["descripcion"] + ' no está definido.'
            raise UserError(_(ERROR))
        if not line_temp["uniMedida"]:
            ERROR = 'La UNIVAD DE MEDIDA del producto  ' + line_temp["descripcion"] + ' no está definido.'
            raise UserError(_(ERROR))

    def check_parametros_dte_fex(self, generacion_dte):
        if not generacion_dte["ambiente"]:
            ERROR = 'El ambiente  no está definido.'
            raise UserError(_(ERROR))
        if not generacion_dte["idEnvio"]:
            ERROR = 'El IDENVIO  no está definido.'
            raise UserError(_(ERROR))        
        if not generacion_dte["documento"]:
            ERROR = 'El DOCUMENTO  no está presente.'
            raise UserError(_(ERROR))
        if not generacion_dte["version"]:
            ERROR = 'La version dte no está definida.'
            raise UserError(_(ERROR))
