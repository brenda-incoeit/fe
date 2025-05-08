##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
# from odoo.exceptions import UserError
from odoo.exceptions import UserError, ValidationError
from odoo import fields, models, api, _
import datetime
import os
from xml.dom import minidom
import logging
from lxml import etree
import base64
from OpenSSL import crypto


_logger = logging.getLogger(__name__)

sit_now = datetime.datetime.now()
sit_now = str(sit_now)


try:
    from OpenSSL import crypto
except ImportError:
    crypto = None
import base64
import logging

_logger = logging.getLogger(__name__)


class HaciendaCertificate(models.Model):
    _name = "afipws.certificate"
    _description = "afipws.certificate"
    _rec_name = "alias_id"
    # name = fields.Char('Nombre', required=True)
    alias_id = fields.Many2one(
    # name = fields.Many2one(
        "afipws.certificate_alias",
        ondelete="cascade",
        string="Certificate Alias",
        auto_join=True,
        index=True,
        null=True
    )
    csr = fields.Text(
        "Request Certificate",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Certificate Request in PEM format.",
    )
    crt = fields.Text(
        "Certificate",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Certificate in PEM format.",
    )
    certificate_file = fields.Binary("Upload Certificate")
    certificate_file_name = fields.Char("Upload Certificate",  index=True )
    certificate_file_text = fields.Text("Certificado")

    crt_id = fields.Char(
        "ID de Certificado",
        readonly=True,
    )
    crt_nit = fields.Char(
        "NIT desde el Certificado",
        readonly=True,
        index=True,
    )
    crt_validity_begin = fields.Char(
        "Valido desde",
        readonly=True,
    )
    crt_validity_until = fields.Char(
        "Valido hasta",
        readonly=True,
    )
    crt_organizationName = fields.Char(
        "Organización",
        readonly=True,
    )
    crt_organizationIdentifier = fields.Char(
        "Identificación",
        readonly=True,
    )
    crt_givenName = fields.Char(
        "Representante",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancel", "Cancelled"),
        ],
        "State",
        index=True,
        readonly=True,
        default="draft",
        help="* The 'Draft' state is used when a user is creating a new pair "
        "key. Warning: everybody can see the key."
        "\n* The 'Confirmed' state is used when a certificate is valid."
        "\n* The 'Canceled' state is used when the key is not more used. You "
        "cant use this key again.",
    )
    request_file = fields.Binary(
        "Download Signed Certificate Request",
        compute="_compute_request_file",
        readonly=True,
    )
    request_filename = fields.Char(
        "Filename",
        readonly=True,
        compute="_compute_request_file",
    )

    # @api.depends("csr")
    # def _compute_request_file(self):
    #     for rec in self:
    #         rec.request_filename = "request.csr"
    #         if rec.csr:
    #             rec.request_file = base64.encodestring(self.csr.encode("utf-8"))
    #         else:
    #             rec.request_file = False

    def action_to_draft(self):
        if self.alias_id.state != "confirmed":
        # if self.name.state != "confirmed":
            raise UserError(_("Certificate Alias must be confirmed first!"))
        self.write({"state": "draft"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True

    def action_confirm(self):

        self.verify_crt()
        self.write({"state": "confirmed"})
        return True

    def verify_crt(self):
        # _logger.info("SIT verificando certificado %s", self.certificate_file)
        # _logger.info('SIT certificado (%s)) ',self.certificate_file_original  )
        # _logger.info("SIT verificando certificado %s", type(self.certificate_file))
        # _logger.info("SIT verificando certificado %s", len(self.certificate_file))
        # _logger.info("SIT verificando certificado_text %s", len(self.certificate_file_text))
        _logger.info("SIT verificando certificado_text %s", self.certificate_file_text)

        """
        Verify if certificate is well formed
        """
        for rec in self:
            crt = rec.certificate_file

            # crt = rec.crt
            msg = False

            if not crt:
                msg = _(
                    "Invalid action! Please, set the certification string to "
                    "continue."
                )
            certificate = rec.get_certificate()
            if certificate is None:
                msg = _(
                    "Invalid action! Your certificate string is invalid. "
                    "Check if you forgot the header CERTIFICATE or forgot/ "
                    "append end of lines."
                )
            if msg:
                raise UserError(msg)
        return True

    def sit_action_upload_certificate(self):
        _logger.info("SIT sit_action_upload_certificate: %s, %s, %s", self.id, self.ids, self)

        wizard = self.env['afipws.upload_certificate.wizard'].create({
            'certificate_id': self.id,
        })

        context = dict(self.env.context)
        context.update({'active_ids': self.ids, 'active_model': self._name})

        return {
            'name': _("%s: Agregar conteo" % (self.alias_id.common_name or "Certificado sin nombre")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'afipws.upload_certificate.wizard',
            'res_id': wizard.id,
            'target': 'new',
            'context': context,
        }

    def get_certificate(self):
        """
        Extrae los datos del certificado XML de Hacienda de El Salvador.
        """
        self.ensure_one()

        if not self.certificate_file:
            return None

        try:
            # Decodifica el archivo desde Base64
            file_content = base64.b64decode(self.certificate_file).decode('utf-8')

            # Verifica si el archivo es XML
            if not file_content.strip().startswith('<'):
                raise UserError(_("El archivo cargado no es un XML válido."))

            xml_data = etree.fromstring(file_content.encode('utf-8'))

            # Extrae la información relevante del XML
            cert_info = {
                "id": xml_data.findtext(".//_id"),
                "nit": xml_data.findtext(".//nit"),
                "public_key": xml_data.findtext(".//publicKey/encodied"),
                "private_key": xml_data.findtext(".//privateKey/encodied"),
                "issuer": xml_data.findtext(".//issuer/commonName"),
                "organization": xml_data.findtext(".//subject/organizationName"),
                "valid_from": xml_data.findtext(".//validity/notBefore"),
                "valid_to": xml_data.findtext(".//validity/notAfter"),
            }

            # Validaciones
            if not cert_info["public_key"]:
                raise UserError(_("El certificado XML no contiene una clave pública válida."))

            if not cert_info["private_key"]:
                _logger.warning("El certificado XML no tiene clave privada.")

            _logger.info("Certificado procesado correctamente: %s", cert_info)

            return cert_info

        except Exception as e:
            _logger.error("Error al leer el certificado XML: %s", str(e))
            raise UserError(_("Error al procesar el certificado XML: %s") % str(e))


    @api.onchange('certificate_file')
    def _onchange_file(self):
        """
        Procesa el archivo XML del certificado y extrae la información relevante.
        """
        self._file_isvalid()

        if not self.certificate_file:
            return

        try:
            # Decodifica el archivo
            file_content = base64.b64decode(self.certificate_file).decode('utf-8')

            if not file_content.strip().startswith('<'):
                raise UserError(_("El archivo cargado no es un XML válido."))

            xml_data = etree.fromstring(file_content.encode('utf-8'))

            # Extraer datos del XML
            self.crt_id = xml_data.findtext(".//_id")
            self.crt_nit = xml_data.findtext(".//nit")
            self.crt_validity_begin = datetime.datetime.fromtimestamp(float(xml_data.findtext(".//validity/notBefore")))
            self.crt_validity_until = datetime.datetime.fromtimestamp(float(xml_data.findtext(".//validity/notAfter")))
            self.crt_organizationName = xml_data.findtext(".//subject/organizationName")
            self.crt_organizationIdentifier = xml_data.findtext(".//subject/organizationIdentifier")

            givenNameNode = xml_data.find(".//subject/givenName")
            self.crt_givenName = givenNameNode.text if givenNameNode is not None and givenNameNode.text else "Sin Nombre"

            # Guarda el contenido del certificado en un campo de texto para referencia
            self.certificate_file_text = file_content

            _logger.info("Certificado XML procesado correctamente.")

        except Exception as e:
            _logger.error("Error al procesar el certificado: %s", str(e))
            raise UserError(_("Error al procesar el certificado: %s") % str(e))


    def _file_isvalid(self):
        """
        Verifica que el archivo tenga la extensión correcta y que sea XML.
        """
        if self.certificate_file_name:
            file_extension = self.certificate_file_name.split(".")[-1].lower()
            if file_extension != 'crt':
                raise ValidationError(_("El archivo debe tener la extensión .crt"))

        return True
