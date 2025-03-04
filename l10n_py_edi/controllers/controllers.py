# -*- coding: utf-8 -*-
# from odoo import http


# class L10nPyEdi(http.Controller):
#     @http.route('/l10n_py_edi/l10n_py_edi', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_py_edi/l10n_py_edi/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_py_edi.listing', {
#             'root': '/l10n_py_edi/l10n_py_edi',
#             'objects': http.request.env['l10n_py_edi.l10n_py_edi'].search([]),
#         })

#     @http.route('/l10n_py_edi/l10n_py_edi/objects/<model("l10n_py_edi.l10n_py_edi"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_py_edi.object', {
#             'object': obj
#         })

