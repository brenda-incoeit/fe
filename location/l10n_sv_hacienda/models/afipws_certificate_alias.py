    ##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import os
import requests
from xml.dom.minidom import parse, parseString


try:
    from OpenSSL import crypto
except ImportError:
    crypto = None


import base64

import logging

_logger = logging.getLogger(__name__)


class HaciendaCertificateAlias(models.Model):
    _name = "afipws.certificate_alias"
    _description = "HACIENDA Distingish Name / Alias"
    _rec_name = "common_name"

    """
    Para poder acceder a un servicio, la aplicación a programar debe utilizar
    un certificado de seguridad, que se obtiene en la web de HACIENDA. Entre otras
    cosas, el certificado contiene un Distinguished Name (DN) que incluye una
    CUIT. Cada DN será identificado por un "alias" o "nombre simbólico",
    que actúa como una abreviación.
    EJ alias: HACIENDA WS Prod - ADHOC SA
    EJ DN: C=ar, ST=santa fe, L=rosario, O=adhoc s.a., OU=it,
           SERIALNUMBER=CUIT 30714295698, CN=afip web services - adhoc s.a.
    """

    common_name = fields.Char(
    "Common Name",
    size=64,
    default="HACIENDA WS",
    help="Just a name, you can leave it this way",
    readonly=False,
    states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},
)
    key = fields.Text(
        "Private Key",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    key_file = fields.Binary("Upload Clave")
    key_file_name = fields.Char("Upload Clave",  index=True )
    key_file_text = fields.Text("Clave")

    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},        readonly=True,
        default=lambda self: self.env.company,
        auto_join=True,
        index=True,
    )
    country_id = fields.Many2one(
        "res.country",
        "Country",
        states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},        readonly=True,
        
        required=False,
    )
    state_id = fields.Many2one(
        "res.country.state",
        "State",
        states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},        readonly=True,
    )
    city = fields.Char(
        "City",
        states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},        readonly=True,
        required=False,
    )
    department = fields.Char(
        "Department",
        default="IT",
        states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},        readonly=True,
        required=True,
    )
    cuit = fields.Char(
        "CUIT",
        compute="_compute_cuit",
        required=True,
    )
    company_cuit = fields.Char(
        "Company CUIT",
        size=16,
        states={"confirmed": [("readonly", True)], "cancel": [("readonly", True)]},        readonly=True,
    )
    # service_provider_cuit = fields.Char(
    #     "Service Provider CUIT",
    #     size=16,
    #     states={"draft": [("readonly", False)]},
    #     readonly=True,
    # )
    certificate_ids = fields.One2many(
        "afipws.certificate",
        "alias_id",
        # "name",
        "Certificates",
        states={"cancel": [("readonly", True)]},
        auto_join=True,
    )
    # service_type = fields.Selection(
    #     [("in_house", "In House"), ("outsourced", "Outsourced")],
    #     "Service Type",
    #     default="in_house",
    #     required=True,
    #     readonly=True,
    #     states={"draft": [("readonly", False)]},
    # )
    state = fields.Selection(
        [
            ("draft", "Draftt"),
            ("confirmed", "Confirmedd"),
            ("cancel", "Cancelledd"),
        ],
        "Statuss",
        index=True,
        readonly=True,
        default="draft",
        help="* The 'Draftt state is used when a user is creating a new pair "
        "key. Warning: everybody can see the key."
        "\n* The 'Confirmed' state is used when the key is completed with "
        "public or private key."
        "\n* The 'Canceled' state is used when the key is not more used. "
        "You cant use this key again.",
    )
    type = fields.Selection(
        [ ("homologation", "TEST"),("production", "PROD")],
        "Entorno de Hacienda",
        required=True,
        default="homologation",
        readonly=False,
        states={"draft": [("readonly", True)]},
    )

    @api.onchange("company_id")
    def change_company_name(self):
        if self.company_id:
            common_name = "HACIENDA WS %s - %s" % (self.type, self.company_id.name)
            self.common_name = common_name[:50]

    # @api.depends("company_cuit", "service_provider_cuit", "service_type")
    @api.depends("company_cuit")
    def _compute_cuit(self):
        for rec in self:
    #         if rec.service_type == "outsourced":
    #             rec.cuit = rec.service_provider_cuit
    #         else:
                rec.cuit = rec.company_cuit

    @api.onchange("company_id")
    def change_company_id(self):
        if self.company_id:
            self.country_id = self.company_id.country_id.id
            self.state_id = self.company_id.state_id.id
            self.city = self.company_id.city
            self.company_cuit = self.company_id.vat

    def action_confirm(self):
        if not self.key:
            self.generate_key()
        self.write({"state": "confirmed"})
        return True

    def generate_key(self, key_length=2048):
        """ """
        # TODO reemplazar todo esto por las funciones nativas de pyafipws
        directorio='C:/Users/INCOE/Documents/GitHub/fe/location/mnt'
        listado_directorio = os.listdir( directorio) 

        # doc = minidom.parse( directorio + '/PrivateKey_06140902221032.key')


        # for rec in self:
            # k = crypto.PKey()
            # k.generate_key(crypto.TYPE_RSA, key_length)
            # rec.key = crypto.dump_privatekey(crypto.FILETYPE_PEM, k)

    def action_to_draft(self):
        self.write({"state": "draft"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        self.certificate_ids.write({"state": "cancel"})
        return True

    # def action_create_certificate_request(self):
    #     """
    #     TODO agregar descripcion y ver si usamos pyafipsw para generar esto
    #     """
    #     for record in self:
    #         _logger.info("SIT action_create_certificate_request: %s, %s, %s", self.id, self.env.id, self.env.user)
    #         req = crypto.X509Req()
    #         req.get_subject().C = self.country_id.code.encode("ascii", "ignore")
    #         if self.state_id:
    #             req.get_subject().ST = self.state_id.name.encode("ascii", "ignore")
    #         req.get_subject().L = self.city.encode("ascii", "ignore")
    #         req.get_subject().O = self.company_id.name.encode("ascii", "ignore")
    #         req.get_subject().OU = self.department.encode("ascii", "ignore")
    #         req.get_subject().CN = self.common_name.encode("ascii", "ignore")
    #         req.get_subject().serialNumber = "CUIT %s" % self.cuit.encode(
    #             "ascii", "ignore"
    #         )
    #         k = crypto.load_privatekey(crypto.FILETYPE_PEM, self.key)
    #         self.key = crypto.dump_privatekey(crypto.FILETYPE_PEM, k)
    #         req.set_pubkey(k)
    #         req.sign(k, "sha256")
    #         csr = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
    #         vals = {
    #             "csr": csr,
    #             # "alias_id": record.id,
    #             "name": record.id,
    #         }
    #         self.certificate_ids.create(vals)
    #     return True

    @api.constrains("common_name")
    def check_common_name_len(self):
        if self.filtered(lambda x: x.common_name and len(x.common_name) > 50):
            raise ValidationError(
                _("The Common Name must be lower than 50 characters long")
            )


























    @api.onchange('key_file')
    def _onchange_file(self):
        # self.certificate_file_text.unlink()


        directorio='C:/Users/INCOE/Documents/GitHub/fe/location/mnt'
        listado_directorio = os.listdir( directorio) 
        _logger.info("SIT selfl %s, %s", self.id, self.ids)
        _logger.info("SIT directorio actual %s", directorio)
        _logger.info("SIT listado directorio actual %s",listado_directorio  )
         
        self._file_isvalid()
        if self.key_file:
            lines = base64.b64decode(self.key_file).decode('utf-8').split('\r\n')
            _logger.info('SIT line: %s', lines)
            _logger.info('SIT line: --------------------------------- company_id=%s ', self.company_id.vat)
            _logger.info('SIT line: %s', lines[0])
            # self.key_file_text = lines[0]
            nit = self.company_id.vat
            if nit:
                nit = nit.replace("-","")
            if os.path.exists( directorio + '/PrivateKey_' + nit + '.key'):
                os.remove( directorio + '/PrivateKey_' + nit + '.key')
                _logger.info("SIT The file has been deleted successfully")
  
            #with open( directorio + '/PrivateKey_' + nit + '.key', 'w') as f:
            with open(directorio + '/PrivateKey_' + nit + '.key', 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line)
                    f.write('\n')


    def _file_isvalid(self):
        _logger.info("SIT key_file_name = %s", self.key_file_name)
        if self.key_file_name and str(self.key_file_name.split(".")[-1:][0]) != 'key':
            raise ValidationError(_("No se puede cargar un archivo de tipo diferente a .key"))
        return True
