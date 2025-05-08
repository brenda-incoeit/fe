# -*- coding: utf-8 -*-
import site
from odoo import fields, models, api, exceptions
import logging
_logger = logging.getLogger(__name__)

class Company(models.Model):
    # _inherit = 'res.company'
    _inherit = 'ir.sequence'
    
    l10n_latam_journal_id = fields.Many2one('account.journal')
    # l10n_latam_document_type_id =   fields.Many2one('l10n_latam.document.type')    	
    

# SIT 

    def _localization_use_documents(self):
        """ El Salvador  localization use documents """
        self.ensure_one()
        _logger.info('SIT account_fiscal_country_id ' )
        _logger.info('SIT account_fiscal_country_id =%s  ', self.account_fiscal_country_id.code )
        return self.account_fiscal_country_id.code == "SV" or super()._localization_use_documents()

