# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_repr

import logging
_logger = logging.getLogger(__name__)


class sit_account_contingencia(models.Model):
    
    _name = 'account.contingencia1'
    _description = "Entrada de contingencia"

    name = fields.Char(
        string='Number',
        compute='_compute_name', 
        required=True,

        # readonly=False, 
        store=True,
        # copy=False,
        # tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nuevo'),
            ('posted', 'Validado'),
            ('posted_lote', 'Lote Validado'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado',
        required=True,
        readonly=True,
        # copy=False,
        tracking=True,
        default='draft',
    )
    date = fields.Datetime(
        string='Date',
        index=True,
        compute='_compute_date', 
        store=True, 
        required=True, 
        # readonly=False, 
        precompute=True,
        # states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]},
        # copy=False,
        # tracking=True,
    )
    invoice_user_id = fields.Many2one(
        string='Responsable',
        comodel_name='res.users',
        copy=False,
        tracking=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        compute='_compute_company_id', store=True, readonly=False, precompute=True,
        index=True,
    )    
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        # compute='_compute_journal_id', store=True, readonly=False, precompute=True,
        required=True,
        # states={'draft': [('readonly', False)]},
        # check_company=True,
        # domain="[('id', 'in', suitable_journal_ids)]",
    )
    sit_fInicio_hInicio = fields.Datetime("Fecha de Inicio de Contingencia - Hacienda", required=True, help="Asignación de Fecha manual para registrarse en Hacienda", )
    sit_fFin_hFin = fields.Datetime("Fecha de Fin de Contingencia - Hacienda",  help="Asignación de Fecha manual para registrarse en Hacienda", )
    sit_tipo_contingencia = fields.Many2one('account.move.tipo_contingencia.field', string="Tipo de Contingencia")
    sit_tipo_contingencia_otro = fields.Text(string="Especifique el Otro Tipo de Contingencia")
    sit_tipo_contingencia_valores = fields.Char(related="sit_tipo_contingencia.valores", string="Tipo de contingiancia(nombre)")
    sit_facturas_relacionadas = fields.One2many(
        'account.move',
        'sit_factura_de_contingencia',
        string='Facturas relacionadas',
    #     copy=True,
    #     # readonly=True,
    #     states={'draft': [('readonly', False)]},
    )


    sit_estado = fields.Text(string="Estado - Hacienda", default="")
    sit_fechaHora = fields.Datetime("Fecha de Hacienda",  help="Asignación de Fecha manual para registrarse en Hacienda", )
    sit_mensaje = fields.Text(string="Mensaje - Hacienda", default="")
    sit_selloRecibido = fields.Text(string="sello Recibido - Hacienda", default="")
    sit_observaciones=fields.Text("observaciones - Hacienda", default="") 
    hacienda_estado=fields.Text("hacienda estado", default="") 
    sit_json_respuesta = fields.Text("Json de Respuesta", default="") 

    def _compute_company_id(self):
        _logger.info("SIT calculando company_id")
        for move in self:
            company_id = self.env.company
            if company_id != move.company_id:
                move.company_id = company_id

    def _compute_date(self):
        _logger.info("SIT calculando date")
        for move in self:
            if not move.date:
                move.date = fields.Date.context_today(self)

    def _compute_name(self):
        _logger.info("SIT asignando name")
        for record in self:

            import datetime
            FechaEventoContingencia = datetime.datetime.now()
            _logger.info("SIT FechaEventoContingencia = %s (%s)", FechaEventoContingencia, type(FechaEventoContingencia))
            FECHA_EVENTO_CONTINGENCIA = FechaEventoContingencia.strftime('%Y-%m-%d_%H%M%S')
            _logger.info("SIT sit_ccf_ FECHA_EVENTO_CONTINGENCIA = %s", FECHA_EVENTO_CONTINGENCIA)

            NAME = "EVENTO_CONTINGENCIA_" + str(FECHA_EVENTO_CONTINGENCIA)
            record.name = NAME




# ---------------------------------------------------------------------------------------------
    # def action_post_contingencia(self):
    #     '''validamos que partner cumple los requisitos basados en el tipo
    # de documento de la sequencia del diario selecionado
    # FACTURA ELECTRONICAMENTE
    # '''
    #     _logger.info("SIT action_post_contingencia ")
    #     MENSAJE = "SIT Generando Factura de Contingencia = ..." 
    #     raise UserError(_(MENSAJE))        


    def _compute_validation_type_2(self):
        for rec in self:
            if  not rec.afip_auth_code:
                validation_type = self.env["res.company"]._get_environment_type()
                if validation_type == "homologation":
                    try:
                        rec.company_id.get_key_and_certificate(validation_type)
                    except Exception:
                        validation_type = False
                return validation_type
            else:
                return False