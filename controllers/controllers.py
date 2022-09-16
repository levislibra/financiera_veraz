# -*- coding: utf-8 -*-
from openerp import http

# class FinancieraVeraz(http.Controller):
#     @http.route('/financiera_veraz/financiera_veraz/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/financiera_veraz/financiera_veraz/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('financiera_veraz.listing', {
#             'root': '/financiera_veraz/financiera_veraz',
#             'objects': http.request.env['financiera_veraz.financiera_veraz'].search([]),
#         })

#     @http.route('/financiera_veraz/financiera_veraz/objects/<model("financiera_veraz.financiera_veraz"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('financiera_veraz.object', {
#             'object': obj
#         })