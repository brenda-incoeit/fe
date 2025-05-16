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
from datetime import datetime, timedelta
import re

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    hacienda_estado = fields.Char(
        copy=False,
        string="Estado DTE",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_codigoGeneracion = fields.Char(
        copy=False,
        string="Codigo de Generación",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_codigoGeneracion_identificacion = fields.Char(
        copy=False,
        string="Codigo de Generación de Identificación",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_selloRecibido = fields.Char(
        copy=False,
        string="Sello Recibido",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_clasificaMsg = fields.Char(
        copy=False,
        string="Cladificación",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_codigoMsg = fields.Char(
        copy=False,
        string="Codigo de Mensaje",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_descripcionMsg = fields.Char(
        copy=False,
        string="Descripción",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hacienda_observaciones = fields.Char(
        copy=False,
        string="Observaciones",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    afip_auth_mode = fields.Selection(
        [("CAE", "CAE"), ("CAI", "CAI"), ("CAEA", "CAEA")],
        string="AFIP authorization mode",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    afip_auth_code = fields.Char(
        copy=False,
        string="CAE/CAI/CAEA Code",
        readonly=True,
        size=24,
        states={"draft": [("readonly", False)]},
    )
    afip_auth_code_due = fields.Date(
        copy=False,
        readonly=True,
        string="CAE/CAI/CAEA due Date",
        states={"draft": [("readonly", False)]},
    )
    afip_associated_period_from = fields.Date(
        'AFIP Period from'
    )
    afip_associated_period_to = fields.Date(
        'AFIP Period to'
    )
    afip_qr_code = fields.Char(compute="_compute_qr_code", string="AFIP QR code")
    afip_message = fields.Text(
        string="AFIP Message",
        copy=False,
    )
    afip_xml_request = fields.Text(
        string="AFIP XML Request",
        copy=False,
    )
    afip_xml_response = fields.Text(
        string="AFIP XML Response",
        copy=False,
    )
    afip_result = fields.Selection(
        [("", "n/a"), ("A", "Aceptado"), ("R", "Rechazado"), ("O", "Observado")],
        "Resultado",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        help="AFIP request result",
    )
    validation_type = fields.Char(
        "Validation Type",
        compute="_compute_validation_type",
    )
    afip_fce_es_anulacion = fields.Boolean(
        string="FCE: Es anulacion?",
        help="Solo utilizado en comprobantes MiPyMEs (FCE) del tipo débito o crédito. Debe informar:\n"
        "- SI: sí el comprobante asociado (original) se encuentra rechazado por el comprador\n"
        "- NO: sí el comprobante asociado (original) NO se encuentra rechazado por el comprador",
    )
    asynchronous_post = fields.Boolean()
    fecha_facturacion_hacienda = fields.Datetime("Fecha de Facturación - Hacienda",  help="Asignación de Fecha manual para registrarse en Hacienda", )

    name = fields.Char(
        readonly=True,  # Lo dejamos como solo lectura después de ser asignado
        copy=False,
        string="Número de Control",
    )

    @api.onchange('move_type')
    def _onchange_move_type(self):
        # Si el tipo de movimiento es una reversión (out_refund), no se debe permitir modificar el nombre (número de control)
        if self.move_type == 'out_refund' and self.name:
            self._fields['name'].readonly = True
        else:
            self._fields['name'].readonly = False

    @api.onchange('journal_id', 'l10n_latam_document_type_id')
    def _onchange_journal_id(self):
        _logger.info("Cambiando el tipo de documento o el diario")
        # Verifica que el campo 'name' (número de control) no se modifique después de haber sido asignado
        if self.name and self.name.startswith("DTE-"):
            _logger.info("El número de control ya ha sido asignado y no debe modificarse.")
            return  # No permite la modificación si ya tiene un número de control asignado

        #if self.journal_id and self.journal_id.type_report == 'ndc':  # Ajusta según tu configuración de tipo de diario
            #self.l10n_latam_document_type_id = self.journal_id.sit_tipo_documento

    #Obtener Número de control
    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("SIT vals list: %s", vals_list)

        today = fields.Date.context_today(self)

        for vals in vals_list:
            name = vals.get('name')

            #Extraer el partner id
            partner_id = vals.get('partner_id')
            if not partner_id:
                for command in vals.get('line_ids', []):
                    if isinstance(command, tuple) and len(command) == 3:
                        line_vals = command[2]
                        partner_id = line_vals.get('partner_id')
                        if partner_id:
                            break

            _logger.info("SIT Partner detectado (desde líneas o principal): %s", partner_id)

            if name and name != '/' and name.startswith('DTE-'):
                _logger.info("SIT create() detecta nombre preasignado o válido: %s", name)
            else:
                journal_id = vals.get('journal_id')
                if not journal_id:
                    raise UserError(_("Debe definir un diario para generar el número de control."))

                journal = self.env['account.journal'].browse(journal_id)
                if not journal.sit_tipo_documento or not journal.sit_tipo_documento.codigo:
                    raise UserError(_("Debe configurar el Tipo de DTE en el diario '%s'.") % journal.name)
                if not journal.sit_codestable:
                    raise UserError(_("Debe configurar el Código de Establecimiento en el diario '%s'.") % journal.name)

                tipo_dte = journal.sit_tipo_documento.codigo
                cod_estable = journal.sit_codestable
                today = fields.Date.context_today(self)
                sequence_code = f'dte.{tipo_dte}'

                _logger.info("SIT Generando número de control desde create() con secuencia=%s, dte=%s, estable=%s",
                             sequence_code, tipo_dte, cod_estable)

                for intento in range(3):
                    numero_control = self.env['ir.sequence'].with_context({
                        'dte': tipo_dte,
                        'estable': cod_estable,
                        'ir_sequence_date': today,
                    }).next_by_code(sequence_code)

                    if not numero_control:
                        raise UserError(
                            _("No se pudo generar número de control con la secuencia '%s'.") % sequence_code)

                    # Comprobamos unicidad *por journal* para evitar colisiones
                    domain = [
                        ('name', '=', numero_control),
                        ('journal_id', '=', journal.id),
                    ]
                    if not self.search_count(domain):
                        vals['name'] = numero_control
                        _logger.info("SIT Número de control generado para diario %s: %s",
                                     journal.name, numero_control)
                        break
                    else:
                        _logger.warning(
                            "SIT Número duplicado detectado en diario %s: %s. Reintentando...",
                            journal.name, numero_control
                        )
                else:
                    raise UserError(_(
                        "No se pudo generar un número de control único después de varios intentos."
                    ))

            if not vals.get('partner_id'):
                raise UserError(_("No se pudo obtener el partner relacionado con el crédito fiscal."))

            #Asignar el codigo de generacion
            if not vals.get('hacienda_codigoGeneracion_identificacion'):
                codigo_generacion = self.sit_generar_uuid()
                vals['hacienda_codigoGeneracion_identificacion'] = codigo_generacion
                _logger.info("Código de generación asignado nuevo: %s", codigo_generacion)
            else:
                _logger.info("Código de generación ya definido, se mantiene: %s",
                             vals['hacienda_codigoGeneracion_identificacion'])

        _logger.info("SIT Partner fin: %s", vals.get('partner_id'))
        self._fields['name'].required = False
        records = super().create(vals_list)

        # ✅ Refuerzo para asegurarte que el name se guarde
        for vals, record in zip(vals_list, records):
            if vals.get('name') and vals['name'] != '/' and record.name == '/':
                record.name = vals['name']
                _logger.info("SIT Refuerzo aplicado. Actualizado name a: %s", vals['name'])

        return records

    @api.depends("move_type")
    def _compute_name(self):
        for rec in self:
            # Si es una reversión (out_refund) y ya tiene un número de control, no permitas que sea modificado.
            if rec.move_type == 'out_refund' and rec.name:
                rec._fields['name'].readonly = True

    def cron_asynchronous_post(self):
        queue_limit = self.env['ir.config_parameter'].sudo().get_param('l10n_sv_haciendaws_fe.queue_limit', 20)
        queue = self.search([
            ('asynchronous_post', '=', True),'|',
            ('afip_result', '=', False),
            ('afip_result', '=', ''),
        ], limit=queue_limit)
        if queue:
            queue._post()

    @api.depends("journal_id", "afip_auth_code")
    def _compute_validation_type(self):
        for rec in self:
            if  not rec.afip_auth_code:
                validation_type = self.env["res.company"]._get_environment_type()
                # if we are on homologation env and we dont have certificates
                # we validate only locally
                _logger.info("SIT validation_type =%s", validation_type)
                if validation_type == "homologation":
                    try:
                        rec.company_id.get_key_and_certificate(validation_type)
                    except Exception:
                        validation_type = False
                rec.validation_type = validation_type
            else:
                rec.validation_type = False
            _logger.info("SIT validtion_type =%s", rec.validation_type)

    @api.depends("afip_auth_code")
    def _compute_qr_code(self):
        for rec in self:
            if rec.afip_auth_mode in ["CAE", "CAEA"] and rec.afip_auth_code:
                number_parts = self._l10n_ar_get_document_number_parts(
                    rec.l10n_latam_document_number, rec.l10n_latam_document_type_id.code
                )

                qr_dict = {
                    "ver": 1,
                    "fecha": str(rec.invoice_date),
                    "cuit": int(rec.company_id.partner_id.l10n_ar_vat),
                    "ptoVta": number_parts["point_of_sale"],
                    "tipoCmp": int(rec.l10n_latam_document_type_id.code),
                    "nroCmp": number_parts["invoice_number"],
                    "importe": float(float_repr(rec.amount_total, 2)),
                    "moneda": rec.currency_id.l10n_ar_afip_code,
                    "ctz": float(float_repr(rec.l10n_ar_currency_rate, 2)),
                    "tipoCodAut": "E" if rec.afip_auth_mode == "CAE" else "A",
                    "codAut": int(rec.afip_auth_code),
                }
                if (
                    len(rec.commercial_partner_id.l10n_latam_identification_type_id)
                    and rec.commercial_partner_id.vat
                ):
                    qr_dict["tipoDocRec"] = int(
                        rec.commercial_partner_id.l10n_latam_identification_type_id.l10n_ar_afip_code
                    )
                    qr_dict["nroDocRec"] = int(
                        rec.commercial_partner_id.vat.replace("-", "").replace(".", "")
                    )
                qr_data = base64.encodestring(
                    json.dumps(qr_dict, indent=None).encode("ascii")
                ).decode("ascii")
                qr_data = str(qr_data).replace("\n", "")
                rec.afip_qr_code = "https://www.afip.gob.ar/fe/qr/?p=%s" % qr_data
            else:
                rec.afip_qr_code = False

    def get_related_invoices_data(self):
        """
        List related invoice information to fill CbtesAsoc.
        """
        self.ensure_one()
        if self.l10n_latam_document_type_id.internal_type == "credit_note":
            return self.reversed_entry_id
        elif self.l10n_latam_document_type_id.internal_type == "debit_note":
            return self.debit_origin_id
        else:
            return self.browse()

    def _get_sequence(self):
        # Regresa una secuencia por cada factura sin usar move.id como clave
        today = fields.Date.context_today(self)
        result = []

        for move in self:
            journal = move.journal_id
            if not journal:
                raise UserError(_("Debe definir un diario."))

            if not journal.sit_tipo_documento or not journal.sit_tipo_documento.codigo:
                raise UserError(_("Debe configurar el Tipo de DTE en el diario '%s'.") % journal.name)
            if not journal.sit_codestable:
                raise UserError(_("Debe configurar el Código de Establecimiento en el diario '%s'.") % journal.name)

            tipo_dte = journal.sit_tipo_documento.codigo
            cod_estable = journal.sit_codestable
            sequence_code = f'dte.{tipo_dte}'

            sequence = self.env['ir.sequence'].with_context({
                'dte': tipo_dte,
                'estable': cod_estable,
                'ir_sequence_date': today,
            }).search([('code', '=', sequence_code)], limit=1)

            if not sequence:
                raise UserError(_("No se encontró la secuencia con código '%s'.") % sequence_code)

            result.append((move, sequence))

        return result

    def _generate_dte_name(self):
        """Genera un número de control único según el diario y secuencia configurada."""
        self.ensure_one()

        journal = self.journal_id
        if not journal:
            raise UserError(_("Debe definir un diario."))

        if not journal.sit_tipo_documento or not journal.sit_tipo_documento.codigo:
            raise UserError(_("Debe configurar el Tipo de DTE en el diario '%s'.") % journal.name)

        if not journal.sit_codestable:
            raise UserError(_("Debe configurar el Código de Establecimiento en el diario '%s'.") % journal.name)

        tipo_dte = journal.sit_tipo_documento.codigo
        cod_estable = journal.sit_codestable
        sequence_code = f'dte.{tipo_dte}'
        today = fields.Date.context_today(self)

        _logger.info("Generando número de control con secuencia %s para dte=%s estable=%s",
                     sequence_code, tipo_dte, cod_estable)

        for intento in range(3):  # evitar duplicados
            numero_control = self.env['ir.sequence'].with_context({
                'dte': tipo_dte,
                'estable': cod_estable,
                'ir_sequence_date': today,
            }).next_by_code(sequence_code)

            if not numero_control:
                raise UserError(_("No se pudo generar un número de control con la secuencia '%s'.") % sequence_code)

            if not self.search_count([('name', '=', numero_control)]):
                _logger.info("Número de control generado exitosamente: %s", numero_control)
                return numero_control
            else:
                _logger.warning("Número de control duplicado detectado: %s. Reintentando...", numero_control)

        raise UserError(_("No se pudo generar un número de control único después de varios intentos."))

    # ---------------------------------------------------------------------------------------------
    def _post(self, soft=True):
        '''validamos que partner cumple los requisitos basados en el tipo
        de documento de la secuencia del diario seleccionado
        FACTURA ELECTRONICAMENTE
        '''
        _logger.info("Iniciando _post para account.move")
        _logger.info("SIT _post llamado con self=%s", self)
        _logger.info("SIT _post llamado con len(self)=%s", len(self))

        if not self:

            if self.move_type == 'out_refund' and self.name:
                _logger.debug("SIT No se puede modificar el número de control después de la reversión.")
                self._fields['name'].readonly = True
                _logger.info(f"El número de control {self.name} no puede ser modificado.")

            _logger.warning("SIT _post llamado sin registros. Posiblemente acción revertir sin contexto válido.")
            move_type = self.env.context.get('default_move_type', 'entry')
            journal_id = self.env.context.get('default_journal_id')

            if not journal_id:
                raise UserError(_("No se puede generar número de control porque no hay contexto de diario definido."))

            if move_type == 'out_refund':
                # ⚠️ Solo crear movimiento temporal si es una nota de crédito
                default_vals = {
                    'journal_id': journal_id,
                    'move_type': move_type,
                }
                temp_move = self.with_context(default_journal_id=journal_id).create([default_vals])
                invoices_to_post = temp_move
                _logger.info("SIT se creó temp_move para out_refund con id=%s y diario=%s", temp_move.id, journal_id)
            else:
                raise UserError(_("No se puede continuar: _post() llamado sin registros y no es out_refund."))
        else:
            invoices_to_post = self

        _logger.debug("SIT Invoice: %s", invoices_to_post)
        for invoice in invoices_to_post:
            _logger.info("SIT Procesando invoice: id=%s, name=%s, move_type=%s", invoice.id, invoice.name,
                         invoice.move_type)

            # Evitar sobrescritura del nombre si ya es válido
            if invoice.name and invoice.name.startswith("DTE-"):
                _logger.debug("SIT Nombre ya asignado correctamente: %s", invoice.name)
                invoice._fields['name'].required = False
                invoice.write({'name': invoice.name})  # No sobrescribir si ya tiene un número de control válido
            else:
                _logger.warning("SIT El número de control está vacío o no es válido.")
                # Si el número de control no es válido o no existe, se genera uno nuevo.
                if not invoice.name or invoice.name == '/' or not invoice.name.startswith("DTE-"):
                    # Generar número de control
                    nombre_generado = invoice._generate_dte_name()
                    if not nombre_generado:
                        raise UserError(_("No se pudo generar un número de control para el documento."))
                    invoice.write({'name': nombre_generado})  # Asignar el nombre generado
                    _logger.info("SIT Nombre de control generado: %s", nombre_generado)

            # Validación de DTE según el tipo de documento y la configuración del diario
            if invoice.move_type in ('out_invoice', 'out_refund'):
                if not invoice.name or invoice.name == '/' or not invoice.name.startswith("DTE-"):
                    raise UserError(_("Número de control no válido o faltante para el documento ID %s.") % invoice.id)

            # Si el tipo de documento requiere validación adicional, hacerlo aquí
            if invoice.journal_id.sit_tipo_documento:
                type_report = invoice.journal_id.type_report
                sit_tipo_documento = invoice.journal_id.sit_tipo_documento.codigo

                _logger.info("SIT action_post type_report = %s", type_report)
                _logger.info("SIT action_post sit_tipo_documento = %s", sit_tipo_documento)
                _logger.info("SIT Receptor = %s, info=%s", invoice.partner_id, invoice.partner_id.parent_id)
                # Validación del partner y otros parámetros según el tipo de DTE
                if type_report == 'ccf':
                    # Validaciones específicas para CCF
                    if not invoice.partner_id.parent_id:
                        if not invoice.partner_id.nrc:
                            invoice.msg_error("N.R.C.")
                        if not invoice.partner_id.vat and not invoice.partner_id.dui:
                            invoice.msg_error("N.I.T O D.U.I.")
                        if not invoice.partner_id.codActividad:
                            invoice.msg_error("Giro o Actividad Económica")
                    else:
                        if not invoice.partner_id.parent_id.nrc:
                            invoice.msg_error("N.R.C.")
                        if not invoice.partner_id.parent_id.vat and not invoice.partner_id.parent_id.dui:
                            invoice.msg_error("N.I.T O D.U.I.")
                        if not invoice.partner_id.parent_id.codActividad:
                            invoice.msg_error("Giro o Actividad Económica")

                elif type_report == 'ndc':
                    # Asignar el partner_id relacionado con el crédito fiscal si no existe parent_id
                    if not invoice.partner_id.parent_id:
                        if not invoice.partner_id.nrc:
                            _logger.info("SIT nrc partner = %s", invoice.partner_id.parent_id)
                            invoice.msg_error("N.R.C.")
                        if not invoice.partner_id.fax:
                            invoice.msg_error("N.I.T.")
                        if not invoice.partner_id.codActividad:
                            invoice.msg_error("Giro o Actividad Económica")
                    else:
                        if not invoice.partner_id.parent_id.nrc:
                            invoice.msg_error("N.R.C.")
                        if not invoice.partner_id.parent_id.fax:
                            invoice.msg_error("N.I.T.")
                        if not invoice.partner_id.parent_id.codActividad:
                            invoice.msg_error("Giro o Actividad Económica")

                ambiente = "00"
                if self._compute_validation_type_2() == 'production':
                    ambiente = "01"
                    _logger.info("SIT Factura de Producción")

                # Firmar el documento y generar el DTE
                payload = invoice.obtener_payload('production', sit_tipo_documento)
                documento_firmado = invoice.firmar_documento('production', payload)

                if documento_firmado:
                    _logger.info("SIT Firmado de documento")
                    payload_dte = invoice.sit_obtener_payload_dte_info(ambiente, documento_firmado)
                    self.check_parametros_dte(payload_dte)
                    Resultado = invoice.generar_dte('production', payload_dte, payload)
                    if Resultado:
                        # Procesar la respuesta de Hacienda
                        dat_time = Resultado['fhProcesamiento']
                        fhProcesamiento = datetime.strptime(dat_time, '%d/%m/%Y %H:%M:%S')
                        invoice.hacienda_estado = Resultado['estado']
                        invoice.hacienda_codigoGeneracion_identificacion = Resultado['codigoGeneracion']
                        invoice.hacienda_selloRecibido = Resultado['selloRecibido']
                        invoice.fecha_facturacion_hacienda = fhProcesamiento + timedelta(hours=6)
                        invoice.hacienda_clasificaMsg = Resultado['clasificaMsg']
                        invoice.hacienda_codigoMsg = Resultado['codigoMsg']
                        invoice.hacienda_descripcionMsg = Resultado['descripcionMsg']
                        invoice.hacienda_observaciones = str(Resultado['observaciones'])
                        codigo_qr = invoice._generar_qr(ambiente, Resultado['codigoGeneracion'],
                                                        invoice.fecha_facturacion_hacienda)
                        invoice.sit_qr_hacienda = codigo_qr
                        invoice.state = "draft"

                        dte = payload['dteJson']
                        invoice.sit_json_respuesta = json.dumps(dte, ensure_ascii=False, default=str)
                        json_str = json.dumps(dte, ensure_ascii=False, default=str)
                        json_base64 = base64.b64encode(json_str.encode('utf-8'))
                        file_name = dte["identificacion"]["numeroControl"] + '.json'
                        invoice.env['ir.attachment'].sudo().create({
                            'name': file_name,
                            'datas': json_base64,
                            'res_model': self._name,
                            'res_id': invoice.id,
                            'mimetype': 'application/json'
                        })
                        _logger.info("SIT JSON creado y adjuntado.")

                else:
                    _logger.info("SIT Documento no firmado")
                    raise UserError(_('SIT Documento NO Firmado'))

        _logger.info("SIT Terminando _post sin procesar ningún DTE (self=%s)", self)
        return super(AccountMove, self)._post()

    def _compute_validation_type_2(self):
        for rec in self:
            parameter_env_type = self.env["ir.config_parameter"].sudo().get_param("afip.ws.env.type")
            if parameter_env_type == "production":
                environment_type = "production"
            else:
                environment_type = "production"
            return environment_type

    # FIMAR FIMAR FIRMAR =======
    def firmar_documento(self, enviroment_type, payload):
        _logger.info("SIT  Firmando de documento")
        _logger.info("SIT Documento a FIRMAR =%s", payload)
        if enviroment_type == 'homologation':
            ambiente = "01"
        else:
            ambiente = "01"
        # host = self.company_id.sit_firmador
        url = "http://192.168.2.25:8113/firmardocumento/"  # host + '/firmardocumento/'
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            payload = {
                "nit": payload["nit"],  # <--- aquí estaba el error, decía 'liendre'
                "activo": True,
                "passwordPri": payload["passwordPri"],
                "dteJson": payload["dteJson"],
            }
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload, default=str))
            _logger.info("SIT firmar_documento response =%s", response.text)
            _logger.info("SIT dte json =%s", json.dumps(payload.get("dteJson", {}), indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            error = str(e)
            _logger.info('SIT error= %s, ', error)
            if "error" in error or "" in error:
                try:
                    error_dict = json.loads(error) if isinstance(error, str) else error
                    MENSAJE_ERROR = str(error_dict.get('status', '')) + ", " + str(error_dict.get('error', '')) + ", " + str(error_dict.get('message', ''))
                except Exception:
                    MENSAJE_ERROR = error
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
            MENSAJE_ERROR = "Código de Error:" + str(status) + ", Codigo:" + str(codigo) + ", Detalle:" + str(
                message)
            raise UserError(_(MENSAJE_ERROR))
        elif json_response['status'] == 'OK':
            status = json_response['status']
            body = json_response['body']
            resultado.append(status)
            resultado.append(body)
            return body

    def obtener_payload(self, enviroment_type, sit_tipo_documento):
        _logger.info("SIT  Obteniendo payload")
        _logger.info("SIT  Tipo de documento= %s", sit_tipo_documento)
        invoice_info = None

        if enviroment_type == 'homologation':
            ambiente = "00"
        else:
            ambiente = "01"
        if sit_tipo_documento in ("01", "13"):
            invoice_info = self.sit_base_map_invoice_info()
            _logger.info("SIT invoice_info FE = %s", invoice_info)
            self.check_parametros_firmado()
        elif sit_tipo_documento == "03":
            invoice_info = self.sit__ccf_base_map_invoice_info()
            _logger.info("SIT invoice_info CCF = %s", invoice_info)
            self.check_parametros_firmado()
        elif sit_tipo_documento == "05":
            invoice_info = self.sit_base_map_invoice_info_ndc()
            self.check_parametros_firmado()
        elif sit_tipo_documento == "11":
            invoice_info = self.sit_base_map_invoice_info_fex()
            _logger.info("SIT invoice_info FEX = %s", invoice_info)
            self.check_parametros_firmado()
        elif sit_tipo_documento == "14":
            invoice_info = self.sit_base_map_invoice_info_fse()
            _logger.info("SIT invoice_info FSE = %s", invoice_info)
            self.check_parametros_firmado()
        _logger.info("SIT payload_data =%s", invoice_info)
        return invoice_info

# FRANCISCO # SE OBTIENE EL JWT Y SE ENVIA A HACIENDA PARA SU VALIDACION
    def generar_dte(self, environment_type, payload, payload_original):
        """
        1) Refresca el token si caducó.
        2) Si no hay JWT en payload['documento'], llama al firmador.
        3) Envía el JWT firmado a Hacienda.
        """
        # ——— 1) Selección de URL de Hacienda ———
        host = 'https://apitest.dtes.mh.gob.sv' if environment_type == 'homologation' else 'https://api.dtes.mh.gob.sv'
        url_receive = f"{host}/fesv/recepciondte"

        # ——— 2) Refrescar token si hace falta ———
        today = fields.Date.context_today(self)

        _logger.info("SIT company_id: %s", self.company_id)
        if not self.company_id.sit_token_fecha or self.company_id.sit_token_fecha.date() < today:
            self.company_id.get_generar_token()

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Odoo',
            'Authorization': f"Bearer {self.company_id.sit_token}",
        }

        # ——— 3) Obtener o firmar el JWT ———
        jwt_token = payload.get('documento')
        if isinstance(jwt_token, str) and jwt_token.strip():
            _logger.info("SIT saltando firma: JWT ya existe")
            _logger.info("SI ME ENCUENTRO EN EL LA CARPETA DE GIT")
        else:
            # Determinar URL del firmador
            firmador_url = getattr(self.company_id, 'sit_firmador', None) \
                           or 'http://192.168.2.25:8113/firmardocumento'

            sign_payload = {
                "nit": payload_original['dteJson']['emisor']['nit'],
                "activo": True,
                "passwordPri": payload_original.get('passwordPri')
                               or self.company_id.sit_password
                               or payload_original['dteJson'].get('passwordPri'),
                "dteJson": payload_original['dteJson'],
            }
            _logger.info("SIT firmando DTE: %s", sign_payload)

            try:
                resp_sign = requests.post(
                    firmador_url,
                    headers={'Content-Type': 'application/json'},
                    json=sign_payload,
                    timeout=30
                )
                resp_sign.raise_for_status()
                data_sign = resp_sign.json()
            except Exception as e:
                raise UserError(_("Error al firmar DTE: %s") % e)

            if data_sign.get('status') != 'OK':
                raise UserError(_("Firma rechazada: %s – %s") %
                                (data_sign.get('status'), data_sign.get('message', 'sin detalle')))

            jwt_token = data_sign['body']
            _logger.info("SIT JWT recibido: %s...", jwt_token[:30])

        # ——— 4) Construir el payload para Hacienda ———
        ident = payload_original['dteJson']['identificacion']
        send_payload = {
            "ambiente": ident['ambiente'],
            "idEnvio": int(self.id),
            "tipoDte": ident['tipoDte'],
            "version": int(ident.get('version', 3)),
            "documento": jwt_token,
            "codigoGeneracion": ident['codigoGeneracion'],
        }
        _logger.info("SIT enviando a MH: %s", send_payload)

        # ——— 5) Envío a Hacienda ———
        try:
            resp = requests.post(url_receive, headers=headers, json=send_payload, timeout=30)
        except Exception as e:
            raise UserError(_("Error de conexión con Hacienda: %s") % e)

        _logger.info("SIT MH status=%s text=%s", resp.status_code, resp.text)
        if resp.status_code != 200:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text or 'sin detalle'
            raise UserError(_("Error MH (HTTP %s): %s") % (resp.status_code, detail))

        data = resp.json()
        estado = data.get('estado')
        if estado == 'RECHAZADO':
            raise UserError(_("Rechazado por MH: %s – %s") %
                            (data.get('clasificaMsg'), data.get('descripcionMsg')))
        if estado == 'PROCESADO':
            return data

        # ——— Caso inesperado ———
        raise UserError(_("Respuesta inesperada de MH: %s") % data)

    def _autenticar(self,user,pwd):
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

    def _generar_qr(self, ambiente, codGen, fechaEmi):
        _logger.info("SIT generando qr = %s", self)
        # enviroment_type = self._get_environment_type()
        # enviroment_type = self.env["res.company"]._get_environment_type()
        enviroment_type =  'homologation'
        if enviroment_type == 'homologation':
            host = 'https://admin.factura.gob.sv'
        else:
            host = 'https://admin.factura.gob.sv'
        fechaEmision =  str(fechaEmi.year) + "-" + str(fechaEmi.month).zfill(2) + "-" + str(fechaEmi.day).zfill(2)
        texto_codigo_qr = host + "/consultaPublica?ambiente=" + str(ambiente) + "&codGen=" + str(codGen) + "&fechaEmi=" + str(fechaEmision)
        _logger.info("SIT generando qr texto_codigo_qr = %s", texto_codigo_qr)
        codigo_qr = qrcode.QRCode(
            version=1,  # Versión del código QR (ajústala según tus necesidades)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Nivel de corrección de errores
            box_size=10,  # Tamaño de los cuadros del código QR
            border=4,  # Ancho del borde del código QR
        )
        codigo_qr.add_data(texto_codigo_qr)
        #os.chdir('C:/Users/INCOE/PycharmProjects/fe/location/mnt/src')
        os.chdir('C:/Users/INCOE/Documents/GitHub/fe/location/mnt/certificado')
        directory = os.getcwd()
        _logger.info("SIT directory =%s", directory)
        basewidth = 100
        buffer = io.BytesIO()
        codigo_qr.make(fit=True)
        img = codigo_qr.make_image(fill_color="black", back_color="white")
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        new_img = img.resize((basewidth,hsize), Image.BICUBIC)
        new_img.save(buffer, format="PNG")
        qrCode = base64.b64encode(buffer.getvalue())
        # self.sit_qr_hacienda = qrCode
        return qrCode

    def generar_qr(self):
        _logger.info("SIT generando qr = %s", self)
        enviroment_type =  'homologation'
        if enviroment_type == 'homologation':
            host = 'https://admin.factura.gob.sv'
            ambiente = "00"
        else:
            host = 'https://admin.factura.gob.sv'
            ambiente = "01"
        texto_codigo_qr = host + "/consultaPublica?ambiente=" + str(ambiente) + "&codGen=" + str(self.hacienda_codigoGeneracion_identificacion) + "&fechaEmi=" + str(self.fecha_facturacion_hacienda)
        codigo_qr = qrcode.QRCode(
            version=1,  # Versión del código QR (ajústala según tus necesidades)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Nivel de corrección de errores
            box_size=10,  # Tamaño de los cuadros del código QR
            border=1,  # Ancho del borde del código QR
        )
        codigo_qr.add_data(texto_codigo_qr)
        os.chdir('C:/Users/INCOE/Documents/GitHub/fe/location/mnt')
        directory = os.getcwd()

        _logger.info("SIT directory =%s", directory)
        basewidth = 100
        buffer = io.BytesIO()

        codigo_qr.make(fit=True)
        img = codigo_qr.make_image(fill_color="black", back_color="white")

        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        new_img = img.resize((basewidth,hsize), Image.BICUBIC)
        new_img.save(buffer, format="PNG")
        qrCode = base64.b64encode(buffer.getvalue())
        self.sit_qr_hacienda = qrCode
        return

    def check_parametros_firmado(self):
        if not self.journal_id.sit_tipo_documento.codigo:
            raise UserError(_('El Tipo de DTE no definido.'))
        if not self.name:
            raise UserError(_('El Número de control no definido'))
        tipo_dte = self.journal_id.sit_tipo_documento.codigo

        if tipo_dte == '01':
            # Solo validar el nombre para DTE tipo 01
            if not self.partner_id.name:
                raise UserError(_('El receptor no tiene NOMBRE configurado para facturas tipo 01.'))
        elif tipo_dte == '03':
            # Validaciones completas para DTE tipo 03
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
            # if not self.partner_id.state_id:
            #     raise UserError(_('El receptor no tiene DEPARTAMENTO configurado.'))
            # if not self.partner_id.munic_id:
            #     raise UserError(_('El receptor no tiene MUNICIPIO configurado.'))
            # if not self.partner_id.email:
            #     raise UserError(_('El receptor no tiene CORREO configurado.'))
        elif tipo_dte == '14':
            # Validaciones completas para DTE tipo 03
            if not self.invoice_date:
                raise UserError(_('Se necesita establecer la fecha de factura.'))

        # Validaciones comunes para cualquier tipo de DTE
        if not self.invoice_line_ids:
            raise UserError(_('La factura no tiene LINEAS DE PRODUCTOS asociada.'))

    def check_parametros_linea_firmado(self, line_temp):
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
