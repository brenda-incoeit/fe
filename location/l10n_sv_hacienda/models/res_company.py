##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
import logging
from odoo.exceptions import UserError
import dateutil.parser
import pytz
import odoo.tools as tools
import os
import hashlib
import time
import sys
import traceback

import requests
from datetime import datetime, timedelta
from . import res_company

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    sit_token = fields.Text('Token ?')
    sit_token_ok = fields.Boolean('Token OK')
    sit_token_user = fields.Char("Usuario Hacienda")
    sit_token_pass = fields.Char("Password Hacienda")
    sit_passwordPri = fields.Char("Password Firmado")
    sit_token_fecha = fields.Datetime(string='Start Date Range', default=datetime.today())
    codActividad = fields.Many2one(related="partner_id.codActividad", string="Actividad Económica")
    nombreComercial = fields.Char(related="partner_id.nombreComercial", string="Nombre Comercial")
    tipoEstablecimiento = fields.Many2one("account.move.tipo_establecimiento.field", string="Tipo de Establecimiento")

    def get_generar_token(self):
        _logger.info("SIT get_generar_token = %s,%s,%s", self.sit_token_user, self.sit_token_pass, self.sit_passwordPri)
        autenticacion = self._autenticar(self.sit_token_user, self.sit_token_pass)
        _logger.info("SIT autenticacioni = %s", autenticacion)
        if not self:
            self = self.env['res.company'].search([('id', '=', 1)])
        self.sit_token = autenticacion
        self.sit_token_fecha = datetime.now()
        self.sit_token_ok = True

    def get_limpiar_token(self):
        self.sit_token_fecha = False
        self.sit_token = ""

    alias_ids = fields.One2many("afipws.certificate_alias", "company_id", "Aliases", auto_join=True)
    connection_ids = fields.One2many("afipws.connection", "company_id", "Connections", auto_join=True)

    @api.model
    def _get_environment_type(self):
        parameter_env_type = self.env["ir.config_parameter"].sudo().get_param("afip.ws.env.type")
        if parameter_env_type == "production":
            environment_type = "production"
        elif parameter_env_type == "homologation":
            environment_type = "homologation"
        else:
            server_mode = tools.config.get("server_mode")
            environment_type = "homologation" if server_mode in ["test", "develop"] else "production"
        _logger.info("Running arg electronic invoice on %s mode" % environment_type)
        return environment_type

    def get_key_and_certificate(self, environment_type):
        self.ensure_one()
        certificate = self.env["afipws.certificate"].search([
            ("alias_id.company_id", "=", self.id),
            ("alias_id.type", "=", environment_type),
            ("state", "=", "confirmed"),
        ])
        certificate1 = certificate.certificate_file_text
        sit_key = self.env["afipws.certificate_alias"].search([
            ("company_id", "=", self.id),
            ("type", "=", environment_type),
            ("state", "=", "confirmed"),
        ])

        if len(certificate) > 1:
            raise UserError(_('Tiene más de un certificado de "%s" confirmado. Por favor deje un solo certificado de "%s" confirmado.') % (environment_type, environment_type))
        if certificate1:
            return sit_key.key_file, certificate1
        else:
            raise UserError(_("No se encontraron certificados confirmados para %s en la compañía %s") % (environment_type, self.name))

    def _autenticar(self, user, pwd):
        _logger.info("SIT user,pwd = %s,%s", user, pwd)

        if not self:
            company_id = self.env['res.company'].search([], limit=1)
            user = company_id.sit_token_user
            pwd = company_id.sit_token_pass

        enviroment_type = self._get_environment_type()
        host = 'https://apitest.dtes.mh.gob.sv' if enviroment_type == 'homologation' else 'https://api.dtes.mh.gob.sv'
        url = host + '/seguridad/auth'
        _logger.info("Url token = %s", url)

        self.check_hacienda_values(user, pwd)

        try:
            payload = {
                "user": user,
                "pwd": pwd
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'MiAplicacionOdoo18/1.0'
            }
            response = requests.post(url, headers=headers, data=payload)
            _logger.info("SIT headers, payload  =%s, %s", headers, payload)
            _logger.info("SIT response =%s", response.text)
        except Exception as e:
            raise UserError(_("Error al autenticar: %s") % str(e))

        json_response = response.json()
        if json_response.get('status') in [401, 402]:
            raise UserError(_("Código de Error: {}, Error: {}, Detalle: {}".format(
                json_response['status'],
                json_response.get('error', ''),
                json_response.get('message', '')
            )))
        elif json_response.get('status') == 'OK':
            token_body = json_response.get('body', {})
            token = token_body.get('token')
            if token and token.startswith("Bearer "):
                token = token[len("Bearer ") :]
            return token
        else:
            raise UserError(_("Error no especificado al autenticar con Hacienda."))

    def check_hacienda_values(self, user, pwd):
        if not user:
            raise UserError(_('Usuario no especificado'))
        if not pwd:
            raise UserError(_('Contraseña no especificada'))

    def test_connection(self):
        self.ensure_one()
        if self.sit_token_ok:
            raise UserError("Token disponible")
        else:
            raise UserError("Token NO disponible")