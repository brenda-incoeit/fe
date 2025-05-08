# -*- coding: utf-8 -*-
# from odoo import http


# class L10nSvHaciendaContingencia(http.Controller):
#     @http.route('/l10n_sv_hacienda_contingencia/l10n_sv_hacienda_contingencia', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_sv_hacienda_contingencia/l10n_sv_hacienda_contingencia/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_sv_hacienda_contingencia.listing', {
#             'root': '/l10n_sv_hacienda_contingencia/l10n_sv_hacienda_contingencia',
#             'objects': http.request.env['l10n_sv_hacienda_contingencia.l10n_sv_hacienda_contingencia'].search([]),
#         })

#     @http.route('/l10n_sv_hacienda_contingencia/l10n_sv_hacienda_contingencia/objects/<model("l10n_sv_hacienda_contingencia.l10n_sv_hacienda_contingencia"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_sv_hacienda_contingencia.object', {
#             'object': obj
#         })
