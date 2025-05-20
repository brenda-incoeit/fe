# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .amount_to_text_sv import to_word
import base64

import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = 'account.move'

    inv_refund_id = fields.Many2one('account.move',
                                    'Factura Relacionada',
                                    copy=False,
                                    track_visibility='onchange')

    state_refund = fields.Selection([
        ('refund', 'Retificada'),
        ('no_refund', 'No Retificada'),
    ],
        string="Retificada",
        index=True,
        readonly=True,
        default='no_refund',
        track_visibility='onchange',
        copy=False)

    amount_text = fields.Char(string=_('Amount to text'),
                              store=True,
                              readonly=True,
                              compute='_amount_to_text',
                              track_visibility='onchange')

    @api.depends('amount_total')
    def _amount_to_text(self):
        for l in self:
            l.amount_text = to_word(l.amount_total)

    def print_pos_retry(self):
        return self.action_invoice_print()

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
        easily the next step of the workflow
    """
        user_admin = self.env.ref("base.user_admin")
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Solo se pueden imprimir facturas."))
        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})

        report = self.journal_id.type_report
        report_xml = self.journal_id.report_xml.xml_id

        if report_xml:
            return self.env.ref(report_xml).with_user(user_admin).report_action(self)

        return self.env.ref('account.account_invoices').with_user(user_admin).report_action(self)

    def msg_error(self, campo):
        raise ValidationError("No puede emitir un documento si falta un campo Legal " \
                              "Verifique %s" % campo)

    def _post(self, soft=True):
        '''validamos que partner cumple los requisitos basados en el tipo
        de documento de la sequencia del diario selecionado'''
        for invoice in self:
            if invoice.move_type != 'entry':
                type_report = invoice.journal_id.type_report

                if type_report == 'fcf':
                    if not invoice.partner_id.parent_id:
                        if not invoice.partner_id.vat:
                            #invoice.msg_error("N.I.T.")
                            pass
                        if invoice.partner_id.company_type == 'person':
                            if not invoice.partner_id.dui:
                                #invoice.msg_error("D.U.I.")
                                pass
                    else:
                        if not invoice.partner_id.parent_id.fax:
                            #invoice.msg_error("N.I.T.")
                            pass
                        if invoice.partner_id.parent_id.company_type == 'person':
                            if not invoice.partner_id.dui:
                                #invoice.msg_error("D.U.I.")
                                pass

                if type_report == 'exp':
                    for l in invoice.invoice_line_ids:
                        if not l.product_id.arancel_id:
                            invoice.msg_error("Posicion Arancelaria del Producto %s" % l.product_id.name)

                # si es retificativa
                if type_report == 'ndc':
                    if not invoice.partner_id.parent_id:
                        if not invoice.partner_id.nrc:
                            invoice.msg_error("N.R.C.")
                        if not invoice.partner_id.fax:
                            invoice.msg_error("N.I.T.")
                        if not invoice.partner_id.codActividad:
                            invoice.msg_error("Actividad Economica")
                    else:
                        if not invoice.partner_id.parent_id.nrc:
                            invoice.msg_error("N.R.C.")
                        if not invoice.partner_id.parent_id.fax:
                            invoice.msg_error("N.I.T.")
                        if not invoice.partner_id.parent_id.codActividad:
                            invoice.msg_error("Actividad Economica")

        return super(AccountMove, self)._post()

#--------------------------------------------------------------------------------------------------------- 

    def sit_action_send_mail(self):
        _logger.info("SIT enviando correo = %s", self)
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        #self.ensure_one()
        #template = self.env.ref(self._get_mail_template_sv(), raise_if_not_found=False)
        #lang = False
        #if template:
        #    lang = template._render_lang(self.ids)[self.id]
        #if not lang:
        #    lang = get_lang(self.env).code
        #compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        #ctx = dict(
        #    default_model='account.move',
        #    default_res_id=self.id,
        #    default_res_model='account.move',
        #    default_use_template=bool(template),
        #    default_template_id=template and template.id or False,
        #    default_composition_mode='comment',
        #    default_is_print=False,
        #    mark_invoice_as_sent=True,
        #    default_email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
        #    model_description=self.with_context(lang=lang).type_name,
        #    force_email=True,
        #    active_ids=self.ids,
        #)
#
        #report_action = {
        #    'name': _('Enviar Factura_por email'),
        #    'type': 'ir.actions.act_window',
        #    'view_type': 'form',
        #    'view_mode': 'form',
        #    'res_model': 'account.invoice.send',
        #    'views': [(compose_form.id, 'form')],
        #    'view_id': compose_form.id,
        #    'target': 'new',
        #    'context': ctx,
        #}
#
        #if self.env.is_admin() and not self.env.company.external_report_layout_id and not self.env.context.get('discard_logo_check'):
        #    return self.env['ir.actions.report']._action_configure_external_report_layout(report_action)
        #return report_action

        template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        
        print(template)

        invoice = self.env['account.move'].browse(self.id)
        print(invoice)
        report = invoice.journal_id.report_xml
        report_xml = invoice.journal_id.report_xml.xml_id
        if report_xml:
            user_admin = self.env.ref("base.user_admin")
            compo = self.env.ref(report_xml).with_user(user_admin).report_action(self)
            #print(report)
            #res = report.with_context().sudo()._render_qweb_pdf(report.id)
            res = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report_xml, [invoice.id])[0]
            #print(compo)
            #print(res)
            #attachment1 = self.env['ir.attachment'].create({
            #    'name': invoice.name + '.pdf',
            #    'type': 'binary',
            #    'datas': base64.encodebytes(res),
            #    'res_model': 'account.move',
            #    'res_id': invoice.id,
            #    })                
            #print(attachment1)
        # Verificar si el objeto tiene el atributo 'hacienda_estado'
        if invoice.hacienda_estado == 'PROCESADO':
            domain = [
                ('res_id', '=', invoice.id),
                ('res_model', '=', invoice._name),
                ('name', '=', invoice.name.replace('/', '_') + '.json')]

            xml_file = self.env['ir.attachment'].search(domain, limit=1)
            attachments = template.attachment_ids
            print(attachments)
            if xml_file:
                attachments = []
                attachments.append((invoice.name.replace('/', '_') + '.json', xml_file.datas))
                attachments.append((invoice.name + '.pdf',base64.encodebytes(res)))
                #print(attachments)
            #results[res_id]['attachments'] = attachments
            #template.attachment_ids = [attachment1.id,xml_file.id]

        #template.checkbox_download = False

        if any(not x.is_sale_document(include_receipts=True) for x in self):
            raise UserError(_("You can only send sales documents"))
        
        return {
            'name': _("Send"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.send',
            'target': 'new',
            'context': {
                'active_ids': self.ids,
                'default_mail_template_id': template and template.id or False,
            },
        }

    def _get_mail_template_sv(self):
        """
        :return: the correct mail template based on the current move type
        """
        return (
            'account.email_template_edi_credit_note'
            if all(move.move_type == 'out_refund' for move in self)
            else 'l10n_invoice_sv.sit_email_template_edi_invoice'
            # else 'account.sit_email_template_edi_invoice'
        )
    

class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    def _get_placeholder_mail_attachments_data(self, move):
        """ Returns all the placeholder data.
        Should be extended to add placeholder based on the checkboxes.
        :param: move:       The current move.
        :returns: A list of dictionary for each placeholder.
        * id:               str: The (fake) id of the attachment, this is needed in rendering in t-key.
        * name:             str: The name of the attachment.
        * mimetype:         str: The mimetype of the attachment.
        * placeholder       bool: Should be true to prevent download / deletion.
        """
        if move.invoice_pdf_report_id:
            return []

        filename = move._get_invoice_report_filename()
        #return [{
        #    'id': f'placeholder_{filename}',
        #    'name': filename,
        #    'mimetype': 'application/pdf',
        #    'placeholder': True,
        #}]

        return []

    @api.model
    def _get_invoice_extra_attachments_data(self, move):
        print(")))))))))))))))))))))))))))qqq")
        print(self.env.context.get('active_ids', []))
        invoice = self.env['account.move'].browse(self.env.context.get('active_ids', []))
        print(invoice)
        report = invoice.journal_id.report_xml
        report_xml = invoice.journal_id.report_xml.xml_id
        if report_xml:
            user_admin = self.env.ref("base.user_admin")
            compo = self.env.ref(report_xml).with_user(user_admin).report_action(self)
            res = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report_xml, [invoice.id])[0]
        # Verificar si el objeto tiene el atributo 'hacienda_estado'
        if invoice.hacienda_estado == 'PROCESADO':
            domain = [
                ('name', '=', invoice.name.replace('/', '_') + '.json')]
            xml_file = self.env['ir.attachment'].search(domain, limit=1)
            domain2 = [('res_id', '=', invoice.id),
                ('res_model', '=', invoice._name),
                ('mimetype', '=', 'application/pdf')]
            xml_file2 = self.env['ir.attachment'].search(domain2, limit=1)
            if not xml_file2:
                xml_file2 = self.env['ir.attachment'].create({
                    'name': invoice.name + ' FE' + '.pdf',
                    'type': 'binary',
                    'datas': base64.encodebytes(res),
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                })                
            
            attachments = []
            print(xml_file)
            if xml_file:
                attachments = []
                attachments.append(xml_file)
                attachments.append(xml_file2)

        print(attachments)

        res = [
            {
                'id': attachment.id,
                'name': attachment.name,
                'mimetype': attachment.mimetype,
                'placeholder': False,
                'protect_from_deletion': True,
            }
            for attachment in attachments
        ]

        print(res)
        return res

    @api.depends('enable_download')
    def _compute_checkbox_download(self):
        for wizard in self:
            wizard.checkbox_download = False