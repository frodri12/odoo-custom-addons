# -*- coding: utf-8 -*-
# from odoo import http


# class L10nPy(http.Controller):
#     @http.route('/l10n_aipy/l10n_aipy', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_aipy/l10n_aipy/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_aipy.listing', {
#             'root': '/l10n_aipy/l10n_aipy',
#             'objects': http.request.env['l10n_aipy.l10n_aipy'].search([]),
#         })

#     @http.route('/l10n_aipy/l10n_aipy/objects/<model("l10n_aipy.l10n_aipy"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_aipy.object', {
#             'object': obj
#         })

