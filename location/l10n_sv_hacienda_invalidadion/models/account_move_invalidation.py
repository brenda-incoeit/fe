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
from datetime import datetime, timedelta  # Importando directamente las funciones/clases
import pytz

# from datetime import datetime

_logger = logging.getLogger(__name__)
EXTRA_ADDONS = r'C:\Users\INCOE\Documents\GitHub\fe\location\mnt\extra-addons\src'

class AccountMoveInvalidation(models.Model):
    _name = "account.move.invalidation"

    state = fields.Selection(selection_add=[('annulment', 'Anulado')], ondelete={'annulment': 'cascade'})

    hacienda_estado_anulacion = fields.Char(
        copy=False,
        string="Estado Anulación",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_codigoGeneracion_anulacion = fields.Char(
        copy=False,
        string="Codigo de Generación",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_selloRecibido_anulacion = fields.Char(
        copy=False,
        string="Sello Recibido",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_fhProcesamiento_anulacion = fields.Datetime(
        copy=False,
        string="Fecha de Procesamiento - Hacienda",
        help="Asignación de Fecha de procesamiento de anulación",
        readonly=True,
    )
    hacienda_codigoMsg_anulacion = fields.Char(
        copy=False,
        string="Codigo de Mensaje",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_descripcionMsg_anulacion = fields.Char(
        copy=False,
        string="Descripción",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_observaciones_anulacion = fields.Char(
        copy=False,
        string="Observaciones",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    sit_qr_hacienda_anulacion = fields.Binary(
        string="QR Hacienda",
        copy=False,
        readonly=True,
        store=True,
    )

    sit_documento_firmado_invalidacion = fields.Text(
        string="Documento Firmado",
        copy=False,
        readonly=True,
    )

    # CAMPOS INVALIDACION
    sit_invalidar = fields.Boolean('Invalidar ?', copy=False, default=False)
    sit_codigoGeneracion_invalidacion = fields.Char(string="codigoGeneracion", copy=False, store=True)
    sit_fec_hor_Anula = fields.Datetime(string="Fecha de Anulación", copy=False, )

    sit_factura_a_reemplazar = fields.Many2one('account.move', string="Documento que reeemplaza", copy=False)

    # sit_codigoGeneracionR = fields.Char(string="codigoGeneracion que Reemplaza" , copy=False, )
    sit_codigoGeneracionR = fields.Char(related="sit_factura_a_reemplazar.hacienda_codigoGeneracion_identificacion",
                                        string="codigoGeneracion que Reemplaza", copy=False, required=True, default=None, )
    sit_tipoAnulacion = fields.Selection(
        selection='_get_tipo_Anulacion_selection', string="Tipo de invalidacion")
    sit_motivoAnulacion = fields.Char(string="Motivo de invalidacion", copy=False, )
    sit_nombreResponsable = fields.Many2one('res.partner',string="Nombre de la persona responsable de invalidar el DTE", copy=False)

    # fields.Char(string="Nombre de la persona responsable de invalidar el DTE" , copy=False, )
    sit_tipDocResponsable = fields.Char(string="Tipo documento de identificación", copy=False, default="13")
    # sit_numDocResponsable = fields.Char(related="sit_nombreResponsable.dui", string="Número de documento de identificación" , copy=False, )
    sit_numDocResponsable = fields.Char(related="sit_nombreResponsable.vat",
                                        string="Número de documento de identificación", copy=False, )
    # sit_tipo_contingencia_valores = fields.Char(related="sit_tipo_contingencia.valores", string="Tipo de contingiancia(nombre)")

    sit_nombreSolicita = fields.Many2one('res.partner', string="Nombre de la persona que solicita invalidar el DTE", copy=False)
    # sit_nombreSolicita = fields.Char(string="Nombre de la persona que solicita invalidar el DTE" , copy=False, )
    sit_tipDocSolicita = fields.Char(string="Tipo documento de identificación solicitante", copy=False, default="13")
    # sit_numDocSolicita = fields.Char(string="Número de documento de identificación solicitante." , copy=False, )
    # sit_numDocSolicita = fields.Char(related="sit_nombreSolicita.dui", string="Número de documento de identificación solicitante" , copy=False, )
    sit_numDocSolicita = fields.Char(related="sit_nombreSolicita.vat",
                                     string="Número de documento de identificación solicitante", copy=False, )

    sit_json_respuesta_invalidacion = fields.Text("Json de Respuesta Invalidacion", default="")


    state = fields.Selection([
        ('draft', 'Borrador'),
        ('annulment', 'Anulado'),
    ], string="Estado", default='draft', tracking=True)

    @api.model
    def _get_tipo_Anulacion_selection(self):
        return [
            ('1', '1-Error en la Información del Documento Tributario Electrónico a invalidar.'),
            ('2', '2-Rescindir de la operación realizada.'),
            ('3', '3-Otro'),
        ]

    # ---------------------------------------------------------------------------------------------
    # ANULAR FACTURA
    # ---------------------------------------------------------------------------------------------
    @api.model
    def button_anul(self):
        '''Generamos la Anulación de la Factura'''
        _logger.info("SIT [INICIO] button_anul para invoices: %s", self.ids)
        # MENSAJE="SIT Respuesta = button_anul"
        # raise UserError(_(MENSAJE))

        # NUMERO_FACTURA= super(AccountMove, self).action_post()
        # _logger.info("SIT NUMERO FACTURA =%s", NUMERO_FACTURA)

        for invoice in self:
            _logger.info("SIT Anulando factura ID: %s, Nombre: %s", invoice.id, invoice.sit_factura_a_reemplazar.name)

            sit_tipo_documento = invoice.sit_factura_a_reemplazar.journal_id.sit_tipo_documento.codigo
            _logger.info("SIT Tipo de documento: %s", sit_tipo_documento)

            fecha_actual = (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-06:00'
            fhProcesamiento = datetime.fromisoformat(fecha_actual)
            fhProcesamiento = fhProcesamiento.astimezone(pytz.timezone('America/El_Salvador')).replace(tzinfo=None)

            #invoice.sit_fec_hor_Anula = fhProcesamiento
            _logger.info("SIT Fecha de anulación registrada: %s", fhProcesamiento)

            if sit_tipo_documento not in ['01', '11']:
                _logger.info("SIT Validando tiempo límite para anulación (24h)")
                fecha_facturacion_hacienda = invoice.sit_factura_a_reemplazar.fecha_facturacion_hacienda
                if fecha_facturacion_hacienda:
                    if isinstance(fecha_facturacion_hacienda, datetime):
                        fecha_factura_dt = fecha_facturacion_hacienda
                    else:
                        fecha_factura_dt = datetime.strptime(fecha_facturacion_hacienda, '%d/%m/%Y %H:%M:%S')

                    fecha_factura_utc = pytz.timezone("America/El_Salvador").localize(fecha_factura_dt).astimezone(
                        pytz.utc)
                    time_diff = datetime.now(pytz.utc) - fecha_factura_utc

                    if time_diff.total_seconds() > 24 * 3600:
                        _logger.warning("SIT Factura excede el límite de anulación de 24h")
                        raise UserError(_("La anulación no puede realizarse. La factura tiene más de 24 horas."))

            if not invoice.hacienda_estado_anulacion:
                if invoice.sit_factura_a_reemplazar.move_type != 'entry':
                    type_report = invoice.sit_factura_a_reemplazar.journal_id.type_report
                    _logger.info("SIT Type report: %s", type_report)

                    validation_type = self._compute_validation_type_2()
                    _logger.info("SIT Validation type: %s", validation_type)

                    ambiente = "00"
                    if validation_type == 'homologation':
                        ambiente = "00"
                        _logger.info("SIT Factura de Prueba")
                    elif validation_type == 'production':
                        _logger.info("SIT Factura de Producción")
                        ambiente = "01"
                    _logger.info("SIT Ambiente: %s", ambiente)

                    payload = invoice.obtener_payload_anulacion(validation_type, sit_tipo_documento)
                    documento_firmado = ""
                    payload_original = payload
                    _logger.info("SIT Payload original de anulación generado")

                    self.check_parametros_invalidacion()

                    if invoice.sit_factura_a_reemplazar.hacienda_selloRecibido:
                        documento_firmado = invoice.firmar_documento_anu(validation_type, payload)
                        _logger.info("SIT Documento firmado exitosamente")
                    elif invoice.sit_factura_a_reemplazar.sit_documento_firmado:
                        documento_firmado = invoice.sit_factura_a_reemplazar.sit_documento_firmado
                        _logger.info("SIT Documento firmado ya existente recuperado")
                    else:
                        MENSAJE = "SIT Factura no contiene Sello de Hacienda por lo que no se puede anular"
                        raise UserError(_(MENSAJE))
                        # _logger.info("SIT documento_firmado recuperado ---------------------------> = %s ", (documento_firmado))

                    if documento_firmado:
                        _logger.info("SIT Firmado de documento")
                        _logger.info("SIT Generando DTE")
                        # Obtiene el payload DTE
                        invoice.sit_documento_firmado_invalidacion = str(documento_firmado)
                        payload_dte = invoice.sit_factura_a_reemplazar.sit_obtener_payload_anulacion_dte_info(ambiente, documento_firmado)
                        MENSAJE = "SIT documento a invalidar firmado = " + str(payload_dte)
                        # raise UserError(_(MENSAJE))
                        self.check_parametros_dte_invalidacion(payload_dte)
                        Resultado = invoice.generar_dte_invalidacion(validation_type, payload_dte, payload_original)

                        import re

                        if Resultado:
                            _logger.info("SIT Respuesta de Hacienda recibida: %s", Resultado)

                            try:
                                dat_time = Resultado['fhProcesamiento']
                                _logger.info("SIT Fecha original de procesamiento: %s", dat_time)

                                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', dat_time):
                                    dat_time = datetime.strptime(dat_time, '%d/%m/%Y %H:%M:%S')
                                    dat_time = dat_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-06:00'
                                elif re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}-\d{4}', dat_time):
                                    dat_time = dat_time[:-2] + ':' + dat_time[-2:]
                                # else:
                                # pass

                                #fhProcesamiento = datetime.fromisoformat(dat_time).replace(tzinfo=None) + timedelta(hours=6)
                                fhProcesamiento = datetime.now(pytz.timezone('America/El_Salvador')).replace(tzinfo=None)

                                _logger.info("SIT Fecha de procesamiento (%s)%s", type(fhProcesamiento), fhProcesamiento)

                                MENSAJE = "SIT Respuesta = " + str(Resultado)
                                invoice.hacienda_estado_anulacion = Resultado['estado']
                                invoice.hacienda_codigoGeneracion_anulacion = Resultado['codigoGeneracion']
                                invoice.hacienda_selloRecibido_anulacion = Resultado['selloRecibido']
                                invoice.hacienda_fhProcesamiento_anulacion = fhProcesamiento

                                invoice.hacienda_codigoMsg_anulacion = Resultado['codigoMsg']
                                invoice.hacienda_descripcionMsg_anulacion = Resultado['descripcionMsg']
                                invoice.hacienda_observaciones_anulacion = str(Resultado['observaciones'])

                                codigo_qr = invoice._generar_qr(ambiente, Resultado['codigoGeneracion'],
                                                                invoice.sit_factura_a_reemplazar.fecha_facturacion_hacienda)
                                #invoice.sit_qr_hacienda_anulacion = codigo_qr
                                _logger.info("SIT Factura creada correctamente =%s", MENSAJE)
                                _logger.info("SIT Factura creada correctamente state =%s", invoice.state)
                                payload_original['dteJson']['firmaElectronica'] = documento_firmado
                                payload_original['dteJson']['selloRecibido'] = Resultado['selloRecibido']
                                _logger.info("SIT Factura creada correctamente payload_original =%s",
                                             str(json.dumps(payload_original)))

                                # invoice.sit_json_respuesta = str(json.dumps(payload_original['dteJson']))
                                print(type(payload_original['dteJson']))
                                invoice.sit_json_respuesta_invalidacion = payload_original['dteJson']
                                _logger.info("SIT JSON de Invalidacion=%s", invoice.sit_json_respuesta_invalidacion)
                                json_str = json.dumps(payload_original['dteJson'])
                                _logger.info("SIT JSON de respuesta guardado")
                                # Codifica la cadena JSON en formato base64
                                json_base64 = base64.b64encode(json_str.encode('utf-8'))

                                invoice.sit_nombreSolicita = invoice.sit_factura_a_reemplazar.partner_id
                                invoice.sit_nombreResponsable = invoice.sit_factura_a_reemplazar.partner_id

                                file_name = 'Invalidacion ' + invoice.sit_factura_a_reemplazar.name.replace('/', '_') + '.json'
                                _logger.info("SIT file_name =%s", file_name)
                                _logger.info("SIT self._name =%s", self._name)
                                _logger.info("SIT invoice.id =%s", invoice.id)
                                invoice.env['ir.attachment'].sudo().create(
                                    {
                                        'name': file_name,
                                        # 'datas': json_response['factura_xml'],
                                        # 'datas': json.dumps(payload_original),
                                        'datas': json_base64,
                                        # 'datas_fname': file_name,
                                        'res_model': self._name,
                                        'res_id': invoice.id,
                                        # 'type': 'binary'
                                        'mimetype': 'application/json'
                                    })
                                _logger.info("SIT json creado........................")

                                invoice.write({
                                    'sit_documento_firmado_invalidacion': str(documento_firmado),
                                    'hacienda_estado_anulacion': Resultado['estado'],
                                    'hacienda_codigoGeneracion_anulacion': Resultado['codigoGeneracion'],
                                    'hacienda_selloRecibido_anulacion': Resultado['selloRecibido'],
                                    'hacienda_fhProcesamiento_anulacion': fhProcesamiento,
                                    'hacienda_codigoMsg_anulacion': Resultado['codigoMsg'],
                                    'hacienda_descripcionMsg_anulacion': Resultado['descripcionMsg'],
                                    'hacienda_observaciones_anulacion': str(Resultado['observaciones']),
                                    'sit_json_respuesta_invalidacion': invoice.sit_json_respuesta_invalidacion,
                                    'state': 'annulment',
                                })
                                _logger.info("SIT Factura anulada correctamente.")
                            except Exception as e:
                                _logger.exception("SIT Error en el procesamiento de la respuesta de Hacienda:")
                                raise UserError("Ocurrió un error al procesar y guardar la respuesta de Hacienda.")
                    else:
                        _logger.info("SIT  Documento no firmado")
                        raise UserError(_('SIT Documento NO Firmado'))
        _logger.info("SIT [FIN] button_anul")

    def _compute_validation_type_2(self):
        for rec in self:
            validation_type = self.env["res.company"]._get_environment_type()
            _logger.info("SIT _compute_validation_type_2 =%s ", validation_type)
            # if validation_type == "homologation":
            # try:
            # rec.company_id.get_key_and_certificate(validation_type)
            # except Exception:
            # validation_type = False
            return validation_type

    # FIMAR FIMAR FIRMAR =====================================================================================================
    def firmar_documento_anu(self, enviroment_type, payload):
        _logger.info("SIT  Firmando de documento")
        _logger.info("SIT Documento a FIRMAR =%s", payload)
        if enviroment_type == 'homologation':
            ambiente = "00"
        else:
            ambiente = "01"
        # Firmado de documento
        # host = 'http://service-it.com.ar:8113'
        # host = 'http://svfe-api-firmador:8113'
        host = "http://192.168.2.25:8113"
        url = host + '/firmardocumento/'
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            MENSAJE = "SIT POST, " + str(url) + ", headers=" + str(headers) + ", data=" + str(json.dumps(payload))
            _logger.info("SIT A FIRMAR = %s", MENSAJE)
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            # _logger.info("SIT firmar_documento response =%s", response.text)
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)
            if "error" in error or "" in error:
                MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) + ", " + str(error['message'])
                raise UserError(_(MENSAJE_ERROR))
            else:
                raise UserError(_(error))
        resultado = []
        json_response = response.json()
        if json_response['status'] in [400, 401, 402]:
            _logger.info("SIT Error 40X  =%s", json_response['status'])
            status = json_response['status']
            error = json_response['error']
            message = json_response['message']
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) + ", Detalle:" + str(message)
            raise UserError(_(MENSAJE_ERROR))
        if json_response['status'] in ['ERROR', 401, 402]:
            _logger.info("SIT Error 40X  =%s", json_response['status'])
            status = json_response['status']
            body = json_response['body']
            codigo = body['codigo']
            message = body['mensaje']
            resultado.append(status)
            resultado.append(codigo)
            resultado.append(message)
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Codigo:" + str(codigo) + ", Detalle:" + str(message)
            raise UserError(_(MENSAJE_ERROR))
        elif json_response['status'] == 'OK':
            status = json_response['status']
            body = json_response['body']
            resultado.append(status)
            resultado.append(body)
            return body

    def obtener_payload_anulacion(self, enviroment_type, sit_tipo_documento):
        _logger.info("SIT  Obteniendo payload")
        if enviroment_type == 'homologation':
            ambiente = "00"
        else:
            ambiente = "01"
        invoice_info = self.sit_factura_a_reemplazar.sit_anulacion_base_map_invoice_info()
        _logger.info("SIT invoice_info FINVALIDACION = %s", invoice_info)
        self.check_parametros_firmado_anu()

        _logger.info("SIT payload_data =%s", invoice_info)
        return invoice_info

    def generar_dte_invalidacion(self, enviroment_type, payload, payload_original):
        _logger.info("SIT  Generando DTE Invalidacion =%s", payload)
        if enviroment_type == 'homologation':
            # host = 'https://apitest.dtes.mh.gob.sv'
            host = "https://api.dtes.mh.gob.sv"
        else:
            host = "https://api.dtes.mh.gob.sv"
        url = host + '/fesv/anulardte'
        agente = self.sit_factura_a_reemplazar.company_id.sit_token_user
        authorization = self.sit_factura_a_reemplazar.company_id.sit_token

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Odoo',  # agente,
            'Authorization': f"Bearer {self.sit_factura_a_reemplazar.company_id.sit_token}"  # authorization
        }
        try:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            _logger.info("SIT generar_dte_invalidacion DTE response =%s", response)
            _logger.info("SIT generar_dte_invalidacion DTE response =%s", response.status_code)
            _logger.info("SIT generar_dte_invalidacion DTE response.text =%s", response.text)
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)
            if "error" in error or "" in error:
                MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) + ", " + str(error['message'])
                raise UserError(_(MENSAJE_ERROR))
            else:
                raise UserError(_(error))
        resultado = []
        _logger.info("SIT generar_dte_invalidacion DTE decodificando respuestas invalidacion")
        # status = json_response.get('status')

        if response.status_code in [400, 401]:
            MENSAJE_ERROR = "ERROR de conexión : " + str(response.text) + " ((( " + str(
                json.dumps(payload_original)) + " )))"
            raise UserError(_(MENSAJE_ERROR))

        json_response = response.json()
        _logger.info("SIT json_response =%s", json_response)
        if json_response['estado'] in ["RECHAZADO", 402]:
            status = json_response['estado']
            ambiente = json_response['ambiente']
            if json_response['ambiente'] == '00':
                ambiente = 'TEST'
            else:
                ambiente = 'PROD'
            clasificaMsg = json_response['clasificaMsg']
            message = json_response['descripcionMsg']
            observaciones = json_response['observaciones']
            MENSAJE_ERROR = "Código de Error..:" + str(
                status) + ", Ambiente:" + ambiente + ", ClasificaciónMsje:" + str(
                clasificaMsg) + ", Descripcion:" + str(message) + ", Detalle:" + str(observaciones) + ", DATA:  " + str(
                json.dumps(payload_original))
            self.hacienda_estado_anulacion = status

            # MENSAJE_ERROR = "Código de Error:" + str(status) + ", Ambiente:" + ambiente + ", ClasificaciónMsje:" + str(clasificaMsg) +", Descripcion:" + str(message) +", Detalle:" +  str(observaciones)
            raise UserError(_(MENSAJE_ERROR))
        status = json_response.get('status')
        if status and status in [400, 401, 402]:
            _logger.info("SIT Error 40X  =%s", status)
            error = json_response.get('error',
                                      'Error desconocido')  # Si 'error' no existe, devuelve 'Error desconocido'
            message = json_response.get('message',
                                        'Mensaje no proporcionado')  # Si 'message' no existe, devuelve 'Mensaje no proporcionado'
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Error:" + str(error) + ", Detalle:" + str(message)
            raise UserError(_(MENSAJE_ERROR))
        if json_response['estado'] in ["PROCESADO"]:
            return json_response

    def _autenticar(self,user,pwd,):
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
            # 'user=06140902221032&pwd=D%237k9r%402mP1!b'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.request("POST", url, headers=headers, data=payload)

            _logger.info("SIT response =%s", response.text)
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)
            if "error" in error or "" in error:
                MENSAJE_ERROR = str(error['status']) + ", " + str(error['error']) + ", " + str(error['message'])
                raise UserError(_(MENSAJE_ERROR))
            else:
                raise UserError(_(error))
        resultado = []
        json_response = response.json()

    def _generar_qr(self, ambiente, codGen, fechaEmi):
        _logger.info("SIT generando qr___ = %s", self)
        # enviroment_type = self._get_environment_type()
        # enviroment_type = self.env["res.company"]._get_environment_type()
        enviroment_type = 'homologation'
        if enviroment_type == 'homologation':
            host = 'https://admin.factura.gob.sv'

        else:
            host = 'https://admin.factura.gob.sv'

        # https://admin.factura.gob.sv/consultaPublica?ambiente=00&codGen=00000000-0000-00000000-000000000000&fechaEmi=2022-05-01
        fechaEmision = str(fechaEmi.year) + "-" + str(fechaEmi.month).zfill(2) + "-" + str(fechaEmi.day).zfill(2)
        texto_codigo_qr = host + "/consultaPublica?ambiente=" + str(ambiente) + "&codGen=" + str(
            codGen) + "&fechaEmi=" + str(fechaEmision)
        _logger.info("SIT generando qr texto_codigo_qr = %s", texto_codigo_qr)
        codigo_qr = qrcode.QRCode(
            version=1,  # Versión del código QR (ajústala según tus necesidades)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Nivel de corrección de errores
            box_size=10,  # Tamaño de los cuadros del código QR
            border=4,  # Ancho del borde del código QR
        )
        codigo_qr.add_data(texto_codigo_qr)
        import os

        if os.name == 'nt':  # Windows
            os.chdir(EXTRA_ADDONS)
        else:  # Linux/Unix
            os.chdir('/mnt/extra-addons/src')
        directory = os.getcwd()
        _logger.info("SIT directory =%s", directory)
        basewidth = 100
        buffer = io.BytesIO()

        codigo_qr.make(fit=True)
        img = codigo_qr.make_image(fill_color="black", back_color="white")
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        new_img = img.resize((basewidth, hsize), Image.BICUBIC)
        new_img.save(buffer, format="PNG")
        qrCode = base64.b64encode(buffer.getvalue())
        # self.sit_qr_hacienda = qrCode
        return qrCode

    def generar_qr(self):
        _logger.info("SIT generando qr xxx= %s", self)
        enviroment_type = 'homologation'
        if enviroment_type == 'homologation':
            host = 'https://admin.factura.gob.sv'
            ambiente = "00"
        else:
            host = 'https://admin.factura.gob.sv'
            ambiente = "01"
        texto_codigo_qr = host + "/consultaPublica?ambiente=" + str(ambiente) + "&codGen=" + str(
            self.hacienda_codigoGeneracion_identificacion) + "&fechaEmi=" + str(self.fecha_facturacion_hacienda)
        _logger.info("SIT generando qr xxx texto_codigo_qr= %s", texto_codigo_qr)

        codigo_qr = qrcode.QRCode(
            version=1,  # Versión del código QR (ajústala según tus necesidades)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Nivel de corrección de errores
            box_size=10,  # Tamaño de los cuadros del código QR
            border=1,  # Ancho del borde del código QR
        )
        codigo_qr.add_data(texto_codigo_qr)
        import os

        if os.name == 'nt':  # Windows
            os.chdir(EXTRA_ADDONS)
        else:  # Linux/Unix
            os.chdir('/mnt/extra-addons/src')
        directory = os.getcwd()

        _logger.info("SIT directory =%s", directory)
        basewidth = 100
        buffer = io.BytesIO()

        codigo_qr.make(fit=True)
        img = codigo_qr.make_image(fill_color="black", back_color="white")

        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        new_img = img.resize((basewidth, hsize), Image.BICUBIC)
        new_img.save(buffer, format="PNG")
        qrCode = base64.b64encode(buffer.getvalue())
        self.sit_qr_hacienda = qrCode
        return

    def check_parametros_invalidacion(self):
        if not self.sit_factura_a_reemplazar.name:
            raise UserError(_('El Número de control no definido'))
        if not self.sit_factura_a_reemplazar.company_id.tipoEstablecimiento.codigo:
            raise UserError(_('El tipoEstablecimiento no definido'))

        if not self.sit_tipoAnulacion or self.sit_tipoAnulacion == False:
            raise UserError(_('El tipoAnulacion no definido'))

    def check_parametros_firmado_anu(self):
        if not self.sit_factura_a_reemplazar.journal_id.sit_tipo_documento.codigo:
            raise UserError(_('El Tipo de  DTE no definido.'))
        if not self.sit_factura_a_reemplazar.name:
            raise UserError(_('El Número de control no definido'))
        if not self.sit_factura_a_reemplazar.company_id.sit_passwordPri:
            raise UserError(_('El valor passwordPri no definido'))
        if not self.sit_factura_a_reemplazar.company_id.sit_uuid:
            raise UserError(_('El valor uuid no definido'))
        if not self.sit_factura_a_reemplazar.company_id.vat:
            raise UserError(_('El emisor no tiene NIT configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.company_registry:
            raise UserError(_('El emisor no tiene NRC configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.name:
            raise UserError(_('El emisor no tiene NOMBRE configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.codActividad:
            raise UserError(_('El emisor no tiene CODIGO DE ACTIVIDAD configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.tipoEstablecimiento:
            raise UserError(_('El emisor no tiene TIPO DE ESTABLECIMIENTO configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.state_id:
            raise UserError(_('El emisor no tiene DEPARTAMENTO configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.munic_id:
            raise UserError(_('El emisor no tiene MUNICIPIO configurado.'))
        if not self.sit_factura_a_reemplazar.company_id.email:
            raise UserError(_('El emisor no tiene CORREO configurado.'))

        if not self.sit_factura_a_reemplazar.journal_id.sit_tipo_documento.codigo:
            raise UserError(_('El Tipo de DTE no definido.'))
        if not self.sit_factura_a_reemplazar.name:
            raise UserError(_('El Número de control no definido'))
        # Validaciones para el emisor (comunes para todos los tipos de DTE)
        # ...

        # Validaciones específicas según el tipo de DTE
        tipo_dte = self.sit_factura_a_reemplazar.journal_id.sit_tipo_documento.codigo

        if tipo_dte == '01':
            # Solo validar el nombre para DTE tipo 01
            if not self.sit_factura_a_reemplazar.partner_id.name:
                raise UserError(_('El receptor no tiene NOMBRE configurado para facturas tipo 01.'))
        elif tipo_dte == '03':
            # Validaciones completas para DTE tipo 03
            if not self.sit_factura_a_reemplazar.partner_id.fax and self.sit_factura_a_reemplazar.partner_id.is_company:
                _logger.info("SIT, es compañia se requiere NIT")
                _logger.info("SIT, partner campos requeridos Invalidation=%s", self.partner_id)
                raise UserError(_('El receptor no tiene NIT configurado.'))
            if not self.sit_factura_a_reemplazar.partner_id.nrc and self.sit_factura_a_reemplazar.partner_id.is_company:
                _logger.info("SIT, es compañia se requiere NRC")
                raise UserError(_('El receptor no tiene NRC configurado.'))
            if not self.sit_factura_a_reemplazar.partner_id.name:
                raise UserError(_('El receptor no tiene NOMBRE configurado.'))
            if not self.sit_factura_a_reemplazar.partner_id.codActividad:
                raise UserError(_('El receptor no tiene CODIGO DE ACTIVIDAD configurado.'))
            if not self.sit_factura_a_reemplazar.partner_id.state_id:
                raise UserError(_('El receptor no tiene DEPARTAMENTO configurado.'))
            if not self.sit_factura_a_reemplazar.partner_id.munic_id:
                raise UserError(_('El receptor no tiene MUNICIPIO configurado.'))
            if not self.sit_factura_a_reemplazar.partner_id.email:
                raise UserError(_('El receptor no tiene CORREO configurado.'))

        # Validaciones comunes para cualquier tipo de DTE
        if not self.sit_factura_a_reemplazar.invoice_line_ids:
            raise UserError(_('La factura no tiene LINEAS DE PRODUCTOS asociada.'))

    def check_parametros_dte_invalidacion(self, generacion_dte):
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
