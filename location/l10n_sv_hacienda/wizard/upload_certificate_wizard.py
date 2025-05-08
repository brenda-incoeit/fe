from odoo import fields, api, models
import base64
from xml.dom import minidom
import datetime
import os
import logging
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo import _, fields, api, models

_logger = logging.getLogger(__name__)

class L10nArAfipwsUploadCertificate(models.TransientModel):
    _name = "afipws.upload_certificate.wizard"
    _description = "afipws.upload_certificate.wizard"

    certificate_id = fields.Many2one("afipws.certificate")
    certificate_file = fields.Binary("Upload Certificate", required=True)
    certificate_file_text = fields.Text("Certificado")
    certificate_file_name = fields.Char(
        "Upload Certificate",
        default="Certificado_06142811001040.crt",
    )
    alias_id = fields.Many2one(
        "afipws.certificate_alias",
        string="Alias del certificado",
        domain=[('state', '=', 'confirmed')]
    )
    file_valid = fields.Boolean(string="Archivo Valido?", compute="_compute_file_valid")

    @api.model
    def get_certificate(self):
        _logger.info("🔍 [get_certificate] Ejecutando método.")
        sit_active_id = self.env.context.get('active_id')
        _logger.info("🔍 [get_certificate] active_id: %s", sit_active_id)
        now_timestamp = int(datetime.datetime.now().timestamp())
        _logger.info("🕒 [get_certificate] Timestamp actual: %s", now_timestamp)
        return now_timestamp

    @api.depends('certificate_file')
    def _compute_file_valid(self):
        self.file_valid = bool(self.certificate_file)
        _logger.info("📄 [compute_file_valid] Archivo es válido: %s", self.file_valid)

    def _file_isvalid(self):
        _logger.info("🔎 [file_isvalid] Validando extensión de archivo.")
        if not self.certificate_file_name:
            raise ValidationError(_("Debe proporcionar un nombre de archivo para el certificado."))
        if not self.certificate_file_name.lower().endswith(".crt"):
            raise ValidationError(_("El archivo debe tener la extensión .crt"))
        return True

    @api.onchange("certificate_file")
    def _onchange_file(self):
        _logger.info("📥 [onchange_file] Archivo subido, procesando...")
        if self.certificate_file and not self.certificate_file_name:
            self.certificate_file_name = "Certificado_06142811001040.crt"
        self._file_isvalid()
        try:
            file_content = base64.b64decode(self.certificate_file).decode("utf-8")
            if not file_content.strip().startswith("<"):
                raise UserError(_("El archivo cargado no es un XML válido."))
            self.certificate_file_text = file_content
            _logger.info("✅ [onchange_file] Certificado XML procesado correctamente.")
        except Exception as e:
            _logger.error("❌ [onchange_file] Error al procesar certificado: %s", str(e))
            raise UserError(_("Error al procesar el certificado: %s") % str(e))

    def action_confirm(self):
        _logger.info("🚀 [action_confirm] Iniciando confirmación de certificado.")
        self.ensure_one()

        if not self.certificate_file:
            raise UserError(_("Debe subir un archivo de certificado antes de confirmar."))

        if not self.certificate_file_name:
            self.certificate_file_name = "Certificado_06142811001040.crt"

        try:
            file_content = base64.b64decode(self.certificate_file).decode("utf-8")
            xml_data = etree.fromstring(file_content.encode("utf-8"))

            _logger.info("📤 [action_confirm] Extrayendo datos del XML...")

            alias = self.env["afipws.certificate_alias"].search([("state", "=", "confirmed")], limit=1)
            if not alias:
                raise UserError(_("No hay ningún alias confirmado disponible."))

            cert_info = {
                "alias_id": self.alias_id.id, #"alias_id": 2,  # ⚠️ ID quemado - asegúrate de que este alias exista
                "certificate_file": self.certificate_file,
                "certificate_file_name": self.certificate_file_name,
                "certificate_file_text": file_content,
                "crt_id": xml_data.findtext(".//_id"),
                "crt_nit": xml_data.findtext(".//nit"),
                "crt_validity_begin": datetime.datetime.fromtimestamp(
                    float(xml_data.findtext(".//validity/notBefore"))),
                "crt_validity_until": datetime.datetime.fromtimestamp(
                    float(xml_data.findtext(".//validity/notAfter"))),
                "crt_organizationName": xml_data.findtext(".//subject/organizationName"),
                "crt_organizationIdentifier": xml_data.findtext(".//subject/organizationIdentifier"),
                "crt_givenName": xml_data.findtext(".//subject/givenName") or "Sin Nombre",
            }

            _logger.info("📋 [action_confirm] Datos extraídos del certificado: %s", cert_info)

            if self.certificate_id and not str(self.certificate_id.id).startswith("NewId_"):
                _logger.info("✏️ [action_confirm] Actualizando certificado existente ID=%s", self.certificate_id.id)
                self.certificate_id.write(cert_info)
                self.certificate_id.action_confirm()
            else:
                _logger.info("🆕 [action_confirm] Creando nuevo certificado con alias_id=1")
                new_cert = self.env['afipws.certificate'].create(cert_info)
                new_cert.action_confirm()

            return True

        except Exception as e:
            _logger.error("❌ [action_confirm] Error al procesar el certificado XML: %s", str(e))
            raise UserError(_("Error al procesar el certificado XML: %s") % str(e))

