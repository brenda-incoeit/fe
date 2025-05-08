import requests
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AfipwsConnection(models.Model):
    _name = "afipws.connection"
    _description = "HACIENDA WS Connection"
    _rec_name = "afip_ws"
    _order = "expirationtime desc"

    company_id = fields.Many2one("res.company", "Company", required=True, index=True, auto_join=True)
    uniqueid = fields.Char("Unique ID", readonly=True)
    token = fields.Text("Token", readonly=True)
    sign = fields.Text("Sign", readonly=True)
    generationtime = fields.Datetime("Generation Time", readonly=True)
    expirationtime = fields.Datetime("Expiration Time", readonly=True)
    afip_login_url = fields.Char("HACIENDA Login URL", compute="_compute_afip_urls")
    afip_ws_url = fields.Char("HACIENDA WS URL", compute="_compute_afip_urls")
    type = fields.Selection([("production", "PROD"), ("homologation", "TEST")], "Type", required=True)
    afip_ws = fields.Selection([("ws_svr_uno_uno", "Servicio de Recepción Uno a Uno"), ("ws_svr_lote", "Servicio de Recepción por Lotes"), ("ws_svr_consulta_dte", "Servicio de Consulta DTE Uno a Uno")], "HACIENDA WS", required=True, default="ws_svr_consulta_dte")

    # Control de intentos
    max_attempts = 2  # Límite de intentos

    @api.depends("type", "afip_ws")
    def _compute_afip_urls(self):
        for rec in self:
            rec.afip_login_url = rec.get_afip_login_url(rec.type)
            afip_ws_url = rec.get_afip_ws_url(rec.afip_ws, rec.type)
            if rec.afip_ws and not afip_ws_url:
                raise UserError(_("Webservice %s not supported") % rec.afip_ws)
            rec.afip_ws_url = afip_ws_url

    def get_afip_login_url(self, environment_type):
        # Modificación de URL para usar la API de autenticación correcta
        if environment_type == "production":
            return "http://192.168.2.87:8000/fe/autenticacion/"
        else:
            return "http://192.168.2.87:8000/fe/autenticacion/"

    def get_afip_ws_url(self, hacienda_ws, environment_type):
        hacienda_ws_url = False
        # Similar lógica a tu código anterior para obtener la URL
        if hacienda_ws == "ws_svr_uno_uno":
            hacienda_ws_url = "https://api.dtes.mh.gob.sv/fesv/recepciondte" if environment_type == "production" else "https://apitest.dtes.mh.gob.sv/fesv/recepciondte"
        return hacienda_ws_url

    @api.model
    def authenticate_hacienda(self, user, pwd):
        """
        Método para autenticar al usuario y obtener el token de Hacienda.
        """
        # Inicializamos la variable de intentos en la sesión
        if "auth_attempts" not in self.env.context:
            self.env.context["auth_attempts"] = 0

        if self.env.context["auth_attempts"] >= self.max_attempts:
            raise UserError(_("Se alcanzó el límite de intentos de autenticación permitidos"))

        # URL de autenticación
        auth_url = self.get_afip_login_url(self.type)

        # Headers para la solicitud
        headers = {
            "User-Agent": "MiAplicacionOdoo/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Datos para el cuerpo de la solicitud
        data = {
            "user": user,
            "pwd": pwd,
        }

        try:
            # Realizar solicitud POST a la URL de autenticación
            response = requests.post(auth_url, headers=headers, data=data)

            # Incrementar el contador de intentos
            self.env.context["auth_attempts"] += 1

            if response.status_code == 200:
                response_data = response.json()

                # Verificar que la respuesta sea exitosa
                if response_data.get("status") == "OK":
                    token = response_data["body"].get("token")
                    roles = response_data["body"].get("roles", [])
                    token_type = response_data.get("tokenType", "Bearer")

                    # Guardar el token y roles en el modelo
                    self.token = f"{token_type} {token}"
                    self.sign = response_data["body"].get("sign")
                    self.generationtime = fields.Datetime.now()

                    # Resetear el contador de intentos en caso de éxito
                    self.env.context["auth_attempts"] = 0

                    _logger.info(f"Autenticación exitosa. Token obtenido: {self.token}, Roles: {roles}")

                    # Retornar token y roles
                    return {
                        "status": "success",
                        "token": self.token,
                        "roles": roles,
                    }

                else:
                    raise UserError(_("Error en autenticación: %s") % response_data.get("message", "No especificado"))

            else:
                raise UserError(_("Error al conectar con el servicio de autenticación: %s") % response.status_code)

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error de conexión con el servicio de autenticación: {e}")
            raise UserError(_("Error de conexión con el servicio de autenticación: %s") % str(e))

    def connect(self, user, pwd):
        """
        Método principal de conexión que llamará al método de autenticación.
        """
        self.ensure_one()

        # Intentamos autenticar
        return self.authenticate_hacienda(user, pwd)
