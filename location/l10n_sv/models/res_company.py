# -*- coding: utf-8 -*-
import site
from odoo import fields, models, api, exceptions
import logging
_logger = logging.getLogger(__name__)

class Company(models.Model):
    _inherit = 'res.company'
    
    company_registry = fields.Char(string="N.R.C.")
    giro = fields.Char(string="Giro")
    #Datos de contacto
    fax = fields.Char(string="Fax")
    pbx = fields.Char(string="PBX")
    sit_uuid = fields.Char(string="UUID")
    nrc = fields.Char(related="partner_id.nrc")
    nombre_comercial = fields.Char(string="Nombre Comercial")
        
    @api.onchange('company_registry')
    def change_company_registry(self):
        self.partner_id.nrc = self.company_registry

    @api.onchange('giro')
    def change_giro(self):
        self.partner_id.giro = self.giro
          
    @api.onchange('pbx')
    def change_pbx(self):
        self.partner_id.pbx = self.pbx
        
    @api.onchange('fax')
    def change_fax(self):
        self.partner_id.fax = self.fax

# SIT 

    def _localization_use_documents(self):
        """ El Salvador  localization use documents """
        self.ensure_one()
        _logger.info('SIT account_fiscal_country_id ' )
        _logger.info('SIT account_fiscal_country_id =%s  ', self.account_fiscal_country_id.code )

        return self.account_fiscal_country_id.code == "SV" or super()._localization_use_documents()




    def generar_uuid(self):
        import uuid
        if not self.sit_uuid:
        # Genera un UUID versión 4 (basado en números aleatorios)
            uuid_aleatorio = uuid.uuid4()

            # Convierte el UUID en formato de cadena
            uuid_cadena = str(uuid_aleatorio)

            print("UUID Aleatorio:", uuid_cadena)
            self.sit_uuid = uuid_cadena
