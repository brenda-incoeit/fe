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


class sit_AccountContingencia(models.Model):
    _inherit = "account.contingencia1"


    fechaHoraTransmision = fields.Datetime(
        copy=False,
        string="Fecga/Hora de Transmisión",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )       

# --------CAMPOS LOTE --------------------

    hacienda_estado_lote = fields.Char(
        copy=False,
        string="Estado Lote",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )    
    hacienda_idEnvio_lote = fields.Char(
        copy=False,
        string="Id de Envio Lote",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )       
    hacienda_fhProcesamiento_lote = fields.Datetime(
        copy=False,
        string="Fecga de Procesamiento de Lote",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )       
    hacienda_codigoLote_lote = fields.Char(
        copy=False,
        string="Codigo de Lote",  
        readonly=True,
          )
    hacienda_codigoMsg_lote = fields.Char(
        copy=False,
        string="Codigo de Mensaje",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_descripcionMsg_lote = fields.Char(
        copy=False,
        string="Descripción de Lote",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    
# ---------------------------------------------------------------------------------------------    POST LOTE

    
    def action_lote_generate(self):
        # after validate, send invoice data to external system via http post
        facturas_firmadas = []
        nro_factura = 0
        for invoice in self.sit_facturas_relacionadas:
            nro_factura += 1
            _logger.info('SIT action_lote_generate factura a firmar = %s', invoice.name)
            # firmando = invoice.action_firmado_lote(invoice)
            firmando = invoice.sit_documento_firmado


            
            if firmando:
                facturas_firmadas.append(firmando)
            else:
                MENSAJE = "Factura no firmada =" + str(invoice.name)
                raise UserError(_(MENSAJE))  
            if nro_factura > 20:
                MENSAJE = "Factura firmada =" + str(firmando)
                raise UserError(_(MENSAJE))  

        # MENSAJE = "Facturas firmadas a validar (" + invoice.name + ") = " + str(facturas_firmadas)
        # raise UserError(_(MENSAJE ))


        validation_type = self._compute_validation_type_2()
        ambiente = "00"
        if validation_type == 'homologacioin':
            ambiente = "00"
            _logger.info("SIT Factura de Prueba")
        elif validation_type == 'production':
            _logger.info("SIT Factura de Producción")
            ambiente = "01"            
        emisor = self.company_id.vat
        emisor = emisor.replace("-", "").replace(".", "")


        if not emisor:
            MENSAJE = "SIT Se requiere definir compañia"
            raise UserError(_(MENSAJE ))            
        payload_dte = self.sit_obtener_payload_lote_dte_info(ambiente, facturas_firmadas, emisor)   

        # MENSAJE = "SIT Payload LOTE DTE (" + str(payload_dte) + ")"
        # raise UserError(_(MENSAJE ))
        #Generando el DTE
        dte_lote = self.generar_dte_lote(validation_type,payload_dte, len(facturas_firmadas))


        if dte_lote:

            hacienda_fhProcesamiento_lote  = dte_lote['fhProcesamiento ']
            _logger.info("SIT Fecha de procesamiento (%s)%s", type(hacienda_fhProcesamiento_lote), hacienda_fhProcesamiento_lote)
            hacienda_fhProcesamiento_lote = datetime.strptime(hacienda_fhProcesamiento_lote, '%d/%m/%Y %H:%M:%S')
            _logger.info("SIT Fecha de procesamiento (%s)%s", type(hacienda_fhProcesamiento_lote), hacienda_fhProcesamiento_lote)
            MENSAJE = "hacienda_fhProcesamiento_lote = " + str(hacienda_fhProcesamiento_lote)
            invoice.hacienda_estado_lote = dte_lote['estado']
            invoice.hacienda_idEnvio_lote = dte_lote['idEnvio ']
            invoice.hacienda_fhProcesamiento_lote = hacienda_fhProcesamiento_lote
            invoice.hacienda_codigoLote_lote = dte_lote['codigoLote ']
            invoice.hacienda_codigoMsg_lote = dte_lote['codigoMsg ']
            invoice.hacienda_descripcionMsg_lote = dte_lote['descripcionMsg ']

            invoice.state = "posted_lote"






    def generar_dte_lote(self, enviroment_type, payload, facturas_firmadas):
        _logger.info("SIT  Generando DTE")
        if enviroment_type == 'homologation': 
            host = 'https://apitest.dtes.mh.gob.sv' 
        else:
            host = 'https://api.dtes.mh.gob.sv'
        url = host + '/fesv/recepcionlote/'

        agente = self.company_id.sit_token_user
        authorization = self.company_id.sit_token

        headers = {
         'Content-Type': 'application/json', 
         'User-Agent': agente,
         'Authorization': authorization
        }
        _logger.info("SIT = requests.request(POST, %s, headers=%s, data=%s)", url, headers, json.dumps(payload))
        # response = requests.request("POST", url, headers=headers, data=payload)
        # _logger.info("SIT response generacion DTE = %s", response)
        # _logger.info("SIT response.text generacion DTE = %s", response.text)
        
        # MENSAJE = "SIT response = requests.request( POST , " + str(url) + ", headers=" + str(headers) + ", data= " + str(json.dumps(payload))     
        # raise UserError(_(MENSAJE))

        try:

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
        if response.status_code in [  400,401 ] :
            MENSAJE_ERROR = "ERROR de conexión : " + str(response.text ) + ", FACTURAS=" + str(facturas_firmadas) + ",  PAYLOAD = " + str(json.dumps(payload))  
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

            # MENSAJE_ERROR = "Código de Error:" + str(status) + ", Ambiente:" + ambiente + ", ClasificaciónMsje:" + str(clasificaMsg) +", Descripcion:" + str(message) +", Detalle:" +  str(observaciones)  
            raise UserError(_(MENSAJE_ERROR))

            
        # if json_response['status'] in [  400, 401, 402 ] :
        #     _logger.info("SIT Error 40X  =%s", json_response['status'])
        #     status=json_response['status']
        #     error=json_response['error']
        #     message=json_response['message']
        #     MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) +", Detalle:" +  str(message)  
        #     raise UserError(_(MENSAJE_ERROR))
        # return json_response
        status = json_response.get('status')
        if status and status in [400, 401, 402]:
            _logger.info("SIT Error 40X  =%s", status)
            error = json_response.get('error', 'Error desconocido')  # Si 'error' no existe, devuelve 'Error desconocido'
            message = json_response.get('message', 'Mensaje no proporcionado')  # Si 'message' no existe, devuelve 'Mensaje no proporcionado'
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) + ", Detalle:" + str(message)
            raise UserError(_(MENSAJE_ERROR))
        if json_response['estado'] in [  "PROCESADO" ] :

            return json_response
    




    def sit_obtener_payload_lote_dte_info(self, ambiente, doc_firmado, nitEmisor):
        invoice_info = {}
        invoice_info["ambiente"] = ambiente
        invoice_info["idEnvio"] = self.sit_generar_uuid()
        invoice_info["version"] = 2
        invoice_info["nitEmisor "] = nitEmisor
        invoice_info["documentos "] = doc_firmado

        return invoice_info        



# ---------------------------------------------------------------------------------------------    POST CONTINGENCIA
    def action_post_contingencia(self):
        '''validamos que partner cumple los requisitos basados en el tipo
    de documento de la sequencia del diario selecionado
    FACTURA ELECTRONICAMENTE
    '''
        # NUMERO_FACTURA= super(AccountMove, self).action_post()
        # _logger.info("SIT NUMERO FACTURA =%s", NUMERO_FACTURA)
        _logger.info("SIT Iniciando Validación de Contingencia")
        for invoice in self:
                
                validation_type = self._compute_validation_type_2()
                _logger.info("SIT action_post validation_type = %s", validation_type)




                ambiente = "00"
                if validation_type == 'homologacioin':
                    ambiente = "00"
                    _logger.info("SIT Factura de Prueba")
                elif validation_type == 'production':
                    _logger.info("SIT Factura de Producción")
                    ambiente = "01"
                # Firmado de documento
                documento_firmado = ""
                
                payload_contingencia = invoice.obtener_payload_contingencia(validation_type)


                _logger.info("SIT Generando DTE conteingencia")
                documento_firmado_contingencia = invoice.firmar_documento(validation_type, payload_contingencia)
                payload_dte_contingencia = invoice.sit_obtener_payload_contingencia_dte_info(documento_firmado_contingencia)

                # self.check_parametros_dte(payload_dte)
                Resultado = invoice.generar_dte_contingencia(validation_type, payload_dte_contingencia, payload_contingencia)
                if Resultado:

                    dat_time  = Resultado['fechaHora']
                    _logger.info("SIT Fecha de procesamiento (%s)%s", type(dat_time), dat_time)
                    fechaHora = datetime.strptime(dat_time, '%d/%m/%Y %H:%M:%S')
                    _logger.info("SIT Fecha de procesamiento (%s)%s", type(fechaHora), fechaHora)
                    _logger.info("SIT Fecha de sit_fechaHora (%s)%s", type(invoice.sit_fechaHora), invoice.sit_fechaHora)
                    MENSAJE = "Resultado = " + str(Resultado)
                    invoice.sit_estado = Resultado['estado']
                    invoice.sit_fechaHora = fechaHora
                    invoice.sit_mensaje = Resultado['mensaje']
                    invoice.sit_selloRecibido = Resultado['selloRecibido']
                    invoice.sit_observaciones = Resultado['observaciones']
                    invoice.state = "posted"

                    # raise UserError(_(MENSAJE))






    def _compute_validation_type_2(self):
        for rec in self:
                validation_type = self.env["res.company"]._get_environment_type()
                if validation_type == "homologation":
                    try:
                        rec.company_id.get_key_and_certificate(validation_type)
                    except Exception:
                        validation_type = False
                return validation_type

# FIMAR FIMAR FIRMAR =====================================================================================================    
    def firmar_documento(self, enviroment_type, payload):
        _logger.info("SIT  Firmando de documento")
        _logger.info("SIT Documento a FIRMAR =%s", payload)
        if enviroment_type == 'homologation': 
            ambiente = "00"
        else:
            ambiente = "01"
        # host = 'http://service-it.com.ar:8113'
        host = 'http://svfe-api-firmador:8113'
        url = host + '/firmardocumento/'
        headers = {
            'Content-Type': 'application/json'
            }
        try:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            _logger.info("SIT firmar_documento response =%s", response.text)
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)       
            if "error" in error or "" in error:
                MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) +", " +  str(error['message'])  
                raise UserError(_(MENSAJE_ERROR))
            else:
                raise UserError(_(error))
        resultado = []    
        json_response = response.json()
        if json_response['status'] in [  400, 401, 402 ] :
            _logger.info("SIT Error 40X  =%s", json_response['status'])
            status=json_response['status']
            error=json_response['error']
            message=json_response['message']
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) +", Detalle:" +  str(message)  
            raise UserError(_(MENSAJE_ERROR))
        if json_response['status'] in [ 'ERROR', 401, 402 ] :
            _logger.info("SIT Error 40X  =%s", json_response['status'])
            status=json_response['status']
            body=json_response['body']
            codigo=body['codigo']
            message=body['mensaje']
            resultado.append(status)
            resultado.append(codigo)
            resultado.append(message)
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Codigo:" + str(codigo) +", Detalle:" +  str(message)  
            raise UserError(_(MENSAJE_ERROR))        
        elif json_response['status'] == 'OK':
            status=json_response['status']
            body=json_response['body']
            resultado.append(status)
            resultado.append(body)
            return body

    def obtener_payload_contingencia(self, enviroment_type):
        _logger.info("SIT  Obteniendo payload")
        if enviroment_type == 'homologation': 
            ambiente = "00"
        else:
            ambiente = "01"
        
        self.check_parametros_contingencia()
        invoice_info = self.sit__contingencia_base_map_invoice_info()
        _logger.info("SIT invoice_info CONTINGENCIA = %s", invoice_info)
        



        _logger.info("SIT payload_data =%s", invoice_info)
        return invoice_info

    def generar_dte_contingencia(self, enviroment_type, payload, payload_original):
        _logger.info("SIT  Generando DTE___contingencia")
        if enviroment_type == 'homologation': 
            host = 'https://apitest.dtes.mh.gob.sv' 
        else:
            host = 'https://api.dtes.mh.gob.sv'
        url = host + '/fesv/contingencia'
        agente = self.company_id.sit_token_user
        authorization = self.company_id.sit_token

        headers = {
         'Content-Type': 'application/json', 
         'User-Agent': agente,
         'Authorization': authorization
        }
        _logger.info("SIT contingencia  = requests.request(POST, %s, headers=%s, data=%s)", url, headers, json.dumps(payload))

        try:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            _logger.info("SIT DTE contingencia response =%s", response)
            _logger.info("SIT DTE contingencia response =%s", response.status_code)
            _logger.info("SIT DTE contingencia response.text =%s", response.text)
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
            fechaHora=json_response['fechaHora']
            mensaje=json_response['mensaje']
            selloRecibido=json_response['selloRecibido']
            observaciones=json_response['observaciones']


            MENSAJE_ERROR = "Código de Error..:" + str(status) + ", fechaHora:" + fechaHora + ", mensaje:" + str(mensaje) +", selloRecibido:" + str(selloRecibido) +", observaciones:" +  str(observaciones) +", DATA:  " +  str(json.dumps(payload_original))  
            self.hacienda_estado= status

            # MENSAJE_ERROR = "Código de Error:" + str(status) + ", Ambiente:" + ambiente + ", ClasificaciónMsje:" + str(clasificaMsg) +", Descripcion:" + str(message) +", Detalle:" +  str(observaciones)  
            raise UserError(_(MENSAJE_ERROR))

            
        # if json_response['status'] in [  400, 401, 402 ] :
        #     _logger.info("SIT Error 40X  =%s", json_response['status'])
        #     status=json_response['status']
        #     error=json_response['error']
        #     message=json_response['message']
        #     MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) +", Detalle:" +  str(message)  
        #     raise UserError(_(MENSAJE_ERROR))
        # return json_response
        if response.status_code in [ 400 ]:
            _logger.info("SIT Contingencia Error 40X  =%s", response.status_code)
            message = json_response.get('mensaje', 'Mensaje no proporcionado')  # Si 'message' no existe, devuelve 'Mensaje no proporcionado'
            estado =  json_response.get('estado', 'Estado no proporcionado')
            MENSAJE_ERROR = "Código de Error:" + str(response.status_code)  + ", Detalle:" + str(message) + ", DATA REQUEST = " + str(json.dumps(payload))
            raise UserError(_(MENSAJE_ERROR))

        status = json_response.get('status')
        if status and status in [400, 401, 402]:
            _logger.info("SIT Error 40X  =%s", status)
            error = json_response.get('error', 'Error desconocido')  # Si 'error' no existe, devuelve 'Error desconocido'
            message = json_response.get('message', 'Mensaje no proporcionado')  # Si 'message' no existe, devuelve 'Mensaje no proporcionado'
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) + ", Detalle:" + str(message)
            raise UserError(_(MENSAJE_ERROR))
        _logger.info("SIT  json_response('estado) =%s", json_response['estado'])
        if json_response['estado'] in [  "RECIBIDO" ] :

            return json_response

    def _autenticar(self,
            user,
            pwd,
            ):
        _logger.info("SIT self = %s", self)
        _logger.info("SIT self = %s, %s", user, pwd)
        enviroment_type = self._get_environment_type()
        _logger.info("SIT Modo = %s", enviroment_type)

        if enviroment_type == 'homologation': 
            host = 'https://apitest.dtes.mh.gob.sv' 

        else:
            host = 'https://api.dtes.mh.gob.sv'

        url = host + '/seguridad/auth'
        
        self.check_hacienda_values()

        try:
            payload = "user=" + user + "&pwd=" + pwd
            #'user=06140902221032&pwd=D%237k9r%402mP1!b'
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.request("POST", url, headers=headers, data=payload)

            _logger.info("SIT response =%s", response.text)
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)       
            if "error" in error or "" in error:
                MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) +", " +  str(error['message'])  
                raise UserError(_(MENSAJE_ERROR))
            else:
                raise UserError(_(error))
        resultado = []    
        json_response = response.json()


    



    def check_parametros_contingencia(self):
        if not self.company_id:
            raise UserError(_('El Nombre de la compañía no definido'))        
        if not self.company_id.partner_id.user_id.partner_id.name:
            raise UserError(_('El Nombre de Responsable no definido'))        
        if not self.company_id.partner_id.user_id.partner_id.vat:
            raise UserError(_('El Número de RFC no definido'))        
        if not self.company_id.tipoEstablecimiento.codigo:
            raise UserError(_('El tipoEstablecimiento no definido'))        
        if not self.sit_tipo_contingencia:
            raise UserError(_('El motivoContingencia no definido'))        
        if not self.sit_fFin_hFin:
            raise UserError(_('El campo Fecha de Fin de Contingencia - Hacienda (sit_fFin_hFin) no definido'))        






    def check_parametros_firmado(self):

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
        
        if not self.partner_id.vat:
            if self.partner_id.is_company == True:
                _logger.info("SIT, es compañia se requiere NIT")            
            raise UserError(_('El receptor no tiene NIT configurado.'))
        if not self.partner_id.nrc:
            if self.partner_id.is_company == True:
                _logger.info("SIT, es compañia se requiere NRC")
                raise UserError(_('El receptor no tiene NRC configurado.'))
        if not self.partner_id.name:
            raise UserError(_('El receptor no tiene NOMBRE configurado.'))
        if not self.partner_id.codActividad:
            raise UserError(_('El receptor no tiene CODIGO DE ACTIVIDAD configurado.'))
        # if not self.partner_id.tipoEstablecimiento:
            # raise UserError(_('El receptor no tiene TIPO DE ESTABLECIMIENTO configurado.'))
        if not self.partner_id.state_id:
            raise UserError(_('El receptor no tiene DEPARTAMENTO configurado.'))
        if not self.partner_id.munic_id:
            raise UserError(_('El receptor no tiene MUNICIPIO configurado.'))
        if not self.partner_id.email:
            raise UserError(_('El receptor no tiene CORREO configurado.'))
        if not self.invoice_line_ids:
            raise UserError(_('La factura no tiene LINEAS DE PRODUCTOS asociada.'))

                


    def check_parametros_dte(self, generacion_dte):
        if not generacion_dte["idEnvio"]:
            ERROR = 'El IDENVIO  no está definido.'
            raise UserError(_(ERROR))
        if not generacion_dte["tipoDte"]:
            ERROR = 'El tipoDte  no está definido.'
            raise UserError(_(ERROR))
        if not generacion_dte["documento"]:
            ERROR = 'El DOCUMENTO  no está presente.'
            raise UserError(_(ERROR))
        if not generacion_dte["codigoGeneracion"]:
            ERROR = 'El codigoGeneracion  no está definido.'
            raise UserError(_(ERROR))
