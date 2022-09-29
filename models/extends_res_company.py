# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	veraz_configuracion_id = fields.Many2one('financiera.veraz.configuracion', 'Configuracion Veraz')
