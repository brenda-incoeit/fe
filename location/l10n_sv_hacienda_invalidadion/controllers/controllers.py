# -*- coding: utf-8 -*-
# from odoo import http


# class L10nSvHaciendaInvalidadion(http.Controller):
#     @http.route('/l10n_sv_hacienda_invalidadion/l10n_sv_hacienda_invalidadion', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_sv_hacienda_invalidadion/l10n_sv_hacienda_invalidadion/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_sv_hacienda_invalidadion.listing', {
#             'root': '/l10n_sv_hacienda_invalidadion/l10n_sv_hacienda_invalidadion',
#             'objects': http.request.env['l10n_sv_hacienda_invalidadion.l10n_sv_hacienda_invalidadion'].search([]),
#         })

#     @http.route('/l10n_sv_hacienda_invalidadion/l10n_sv_hacienda_invalidadion/objects/<model("l10n_sv_hacienda_invalidadion.l10n_sv_hacienda_invalidadion"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_sv_hacienda_invalidadion.object', {
#             'object': obj
#         })
