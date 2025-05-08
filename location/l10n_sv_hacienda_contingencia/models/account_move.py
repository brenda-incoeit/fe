# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import pytz
import logging
_logger = logging.getLogger(__name__)
tz_el_salvador = pytz.timezone('America/El_Salvador')

class sit_account_move(models.Model):
    _inherit = 'account.move'
    sit_tipo_contingencia = fields.Many2one('account.move.tipo_contingencia.field', string="Tipo de Contingencia")
    sit_tipo_contingencia_otro = fields.Text(string="Especifique el Otro Tipo de Contingencia")
    sit_tipo_contingencia_valores = fields.Char(related="sit_tipo_contingencia.valores", string="Tipo de contingiancia(nombre)")
    sit_factura_de_contingencia = fields.Many2one('account.contingencia1', string="Factura de contingencia relacionada")
    sit_es_configencia = fields.Boolean('Es contingencia ?',  copy=False,)
    sit_factura_por_lote = fields.Boolean('Facturado por lote ?',  copy=False, default=False)

    @api.onchange('sit_es_configencia')
    def check_sit_es_configencia(self):
        _logger.info("SIT revisando  si es o no es sit_es_configencia   <---------------------------------------------")
        if self.sit_es_configencia:
            _logger.info("SIT sit_es_configencia")
            #self.sit_block_hacienda = True
        else:
            _logger.info("SIT NO sit_es_configencia")                
            #self.sit_block_hacienda = False


# ---------------------------------------------------------------------------------------------
# FACTURA CONTINGENCIA
#---------------------------------------------------------------------------------------------
    def action_post_contingencia(self):
        '''validamos que partner cumple los requisitos basados en el tipo
    de documento de la sequencia del diario selecionado
    FACTURA ELECTRONICAMENTE
    '''
        # NUMERO_FACTURA= super(AccountMove, self).action_post()
        # _logger.info("SIT NUMERO FACTURA =%s", NUMERO_FACTURA)
        for invoice in self:
            MENSAJE = "action_post_contingencia -->" + str(self.name)
            # raise UserError(_(MENSAJE))
            if invoice.name == "/" or not invoice.name:
                NUMERO_FACTURA = invoice._set_next_sequence()
            else:
                NUMERO_FACTURA = "/"
            _logger.info("SIT NUMERO FACTURA =%s", NUMERO_FACTURA)
            if invoice.sit_es_configencia:
                sello_contingencia = invoice.sit_factura_de_contingencia.sit_selloRecibido
                if sello_contingencia:
                    #invoice.sit_block_hacienda = False
                    invoice.action_post()        
                else:
                    #invoice.sit_block_hacienda = True
                    MENSAJE = "Se requiere el sello de contingencia para proceder a validar esta factura"
                    raise UserError(_(MENSAJE))

                if not sello_contingencia:
                    MENSAJE = "Se requiere el sello de contingencia para proceder a validar esta factura"
                    raise UserError(_(MENSAJE))
    

        # for invoice in self:
        #     if invoice.move_type != 'entry':
        #         type_report = invoice.journal_id.type_report
        #         sit_tipo_documento = invoice.journal_id.sit_tipo_documento.codigo
                
        #         _logger.info("SIT action_post type_report  = %s", type_report)
        #         _logger.info("SIT action_post sit_tipo_documento  = %s", sit_tipo_documento)
        #         # _logger.info("SIT action_post sit_tipo_documento  = %s", sit_tipo_documento.codigo)
        #         validation_type = self._compute_validation_type_2()
        #         _logger.info("SIT action_post validation_type = %s", validation_type)
               
        #         if type_report == 'ccf':
        #             if not invoice.partner_id.parent_id:
        #                 if not invoice.partner_id.nrc:
        #                     invoice.msg_error("N.R.C.")
        #                 if not invoice.partner_id.vat and not invoice.partner_id.dui:
        #                     invoice.msg_error("N.I.T O D.U.I.")
        #                 # if not invoice.partner_id.giro:
        #                     # invoice.msg_error("Giro")
        #                 if not invoice.partner_id.codActividad:
        #                     invoice.msg_error("Giro o Actividad Económica")
        #             else:
        #                 if not invoice.partner_id.parent_id.nrc:
        #                     invoice.msg_error("N.R.C.")
        #                 if not invoice.partner_id.parent_id.vat and not invoice.partner_id.parent_id.dui:
        #                     invoice.msg_error("N.I.T O D.U.I.")
        #                 if not invoice.partner_id.parent_id.codActividad:
        #                     invoice.msg_error("Giro o Actividad Económica")

        #         elif type_report == 'fcf':
        #             if not invoice.partner_id.parent_id:
        #                 if not invoice.partner_id.vat:
        #                     #invoice.msg_error("N.I.T.")
        #                     pass
        #                 if invoice.partner_id.company_type == 'person':
        #                     if not invoice.partner_id.dui:
        #                         #invoice.msg_error("D.U.I.")
        #                         pass
        #             else:
        #                 if not invoice.partner_id.parent_id.vat:
        #                     #invoice.msg_error("N.I.T.")
        #                     pass
        #                 if invoice.partner_id.parent_id.company_type == 'person':
        #                     if not invoice.partner_id.dui:
        #                         #invoice.msg_error("D.U.I.")
        #                         pass

        #         elif type_report == 'exp':
        #             for l in invoice.invoice_line_ids:
        #                 if not l.product_id.arancel_id:
        #                     invoice.msg_error("Posicion Arancelaria del Producto %s" % l.product_id.name)

        #         # si es retificativa
        #         elif type_report == 'ndc':
        #             if not invoice.partner_id.parent_id:
        #                 if not invoice.partner_id.nrc:
        #                     invoice.msg_error("N.R.C.")
        #                 if not invoice.partner_id.vat:
        #                     invoice.msg_error("N.I.T.")
        #                 # if not invoice.partner_id.giro:
        #                 #     invoice.msg_error("Giro")
        #                 if not invoice.partner_id.codActividad:
        #                     invoice.msg_error("Giro o Actividad Económica")
        #             else:
        #                 if not invoice.partner_id.parent_id.nrc:
        #                     invoice.msg_error("N.R.C.")
        #                 if not invoice.partner_id.parent_id.vat:
        #                     invoice.msg_error("N.I.T.")
        #                 # if not invoice.partner_id.parent_id.giro:
        #                 #     invoice.msg_error("Giro")
        #                 if not invoice.partner_id.parent_id.codActividad:
        #                     invoice.msg_error("Giro o Actividad Económica")
        #         ambiente = "00"
        #         if validation_type == 'homologation':
        #             ambiente = "00"
        #             _logger.info("SIT Factura de Prueba")
        #         elif validation_type == 'production':
        #             _logger.info("SIT Factura de Producción")
        #             ambiente = "01"
        #         # Firmado de documento
        #         payload = invoice.obtener_payload(validation_type, sit_tipo_documento)
        #         documento_firmado = ""
        #         payload_original = payload
        #         _logger.info("SIT payload_original = %s ", str((payload_original)) ) 


        #         documento_firmado = invoice.firmar_documento(validation_type, payload)
        #         # payload_contingencia = invoice.obtener_payload_contingencia(validation_type, sit_tipo_documento)

        #         if documento_firmado:
        #             _logger.info("SIT Firmado de documento contingencia")
        #             _logger.info("SIT Generando DTE contingencia")
        #             #Obtiene el payload DTE
        #             # raise UserError(_('SIT Documento Firmado, Generando DTE'))
        #             # codigo_qr = invoice._generar_qr(ambiente, invoice.hacienda_codigoGeneracion_identificacion, invoice.fecha_facturacion_hacienda )
        #             invoice.sit_documento_firmado = str(documento_firmado)

        #             # raise UserError(_('SIT Documento Firmado, Generando DTE'))

        #         else:
        #             _logger.info("SIT  Documento no firmado contingencia" )    
        #             raise UserError(_('SIT Documento NO Firmado'))

        #         _logger.info("SIT Generando DTE conteingencia")
        #         sello_contingencia = invoice.sit_factura_de_contingencia.sit_selloRecibido
        #         if sello_contingencia:
        #             payload_dte = invoice.sit_obtener_payload_dte_info(ambiente, documento_firmado)
        #             self.check_parametros_dte(payload_dte)
        #             Resultado = invoice.generar_dte(validation_type, payload_dte, payload_original)
        #             if Resultado:

        #                 dat_time  = Resultado['fhProcesamiento']
        #                 _logger.info("SIT Fecha de procesamiento (%s)%s", type(dat_time), dat_time)
        #                 fhProcesamiento = datetime.strptime(dat_time, '%d/%m/%Y %H:%M:%S')
        #                 _logger.info("SIT Fecha de procesamiento (%s)%s", type(fhProcesamiento), fhProcesamiento)

        #                 MENSAJE="SIT Respuesta = " + str(Resultado)
        #                 invoice.hacienda_estado = Resultado['estado']
        #                 invoice.hacienda_codigoGeneracion_identificacion = Resultado['codigoGeneracion']
        #                 invoice.hacienda_selloRecibido = Resultado['selloRecibido']
        #                 invoice.fecha_facturacion_hacienda = fhProcesamiento        #  Resultado['fhProcesamiento']
        #                 invoice.hacienda_clasificaMsg = Resultado['clasificaMsg']
        #                 invoice.hacienda_codigoMsg = Resultado['codigoMsg']
        #                 invoice.hacienda_descripcionMsg = Resultado['descripcionMsg']
        #                 invoice.hacienda_observaciones = str(Resultado['observaciones'])
        #                 codigo_qr = invoice._generar_qr(ambiente, Resultado['codigoGeneracion'], invoice.fecha_facturacion_hacienda )
        #                 invoice.sit_qr_hacienda = codigo_qr
        #                 _logger.info("SIT Factura creada correctamente =%s", MENSAJE)
        #                 _logger.info("SIT Factura creada correctamente state =%s", invoice.state)
        #                 payload_original['dteJson']['firmaElectronica'] = documento_firmado
        #                 payload_original['dteJson']['selloRecibido'] = Resultado['selloRecibido']
        #                 _logger.info("SIT Factura creada correctamente payload_original =%s",   str(json.dumps(payload_original)))  

        #                 invoice.sit_json_respuesta = str(json.dumps(payload_original['dteJson']))
        #                 json_str = json.dumps(payload_original['dteJson'])
        #                 # Codifica la cadena JSON en formato base64
        #                 json_base64 = base64.b64encode(json_str.encode('utf-8'))

        #                 file_name = invoice.name.replace('/', '_') + '.json'
        #                 _logger.info("SIT file_name =%s", file_name)
        #                 _logger.info("SIT self._name =%s", self._name)
        #                 _logger.info("SIT invoice.id =%s", invoice.id)
        #                 invoice.env['ir.attachment'].sudo().create(
        #                     {
        #                         'name': file_name,
        #                         # 'datas': json_response['factura_xml'],
        #                         # 'datas': json.dumps(payload_original),
        #                         'datas': json_base64,
        #                         # 'datas_fname': file_name,
        #                         'res_model': self._name,
        #                         'res_id': invoice.id,
        #                         # 'type': 'binary'
        #                         'mimetype': 'application/json'
        #                     })
                            
        #                 _logger.info("SIT json creado........................")



        #                 invoice.state = "draft"
        #                 return super(AccountMove, self).action_post()
        #                 # raise UserError(_(MENSAJE))

                    

        #         else:
        #             if invoice.hacienda_codigoGeneracion_identificacion:
        #                 MENSAJE = "Se requiere el sello de contingencia para proceder a validar esta factura"
        #                 raise UserError(_(MENSAJE))
        #             else:
        #                 _logger.info("SIT buscando hacienda_codigoGeneracion_identificacion = %s", payload_original['dteJson']['identificacion'])
        #                 invoice.hacienda_codigoGeneracion_identificacion = payload_original['dteJson']['identificacion']['codigoGeneracion']

        # # return super(AccountMove, self).action_post()
        # return 





