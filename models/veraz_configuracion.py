# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests

ENDPOINT_VERAZ = 'https://ws01.veraz.com/rest/variables'

class FinancieraVerazConfiguracion(models.Model):
	_name = 'financiera.veraz.configuracion'

	name = fields.Char('Nombre')
	token = fields.Char('Token')
	client_id = fields.Char('Cliente ID')
	client_secret = fields.Char('Cliente Secret')
	matriz = fields.Char('Matriz')
	usuario = fields.Char('Usuario')
	password = fields.Char('Password')
	sector = fields.Char('Sector')
	sucursal = fields.Char('Sucursal')
	
	ejecutar_cda_al_solicitar_informe = fields.Boolean('Ejecutar CDAs al solicitar informe')
	solicitar_informe_enviar_a_revision = fields.Boolean('Solicitar informe al enviar a revision')
	vr = fields.Integer('Grupo de variables')
	nro_grupo_vid = fields.Integer('Grupo VID')
	nro_grupo_vid2 = fields.Integer('Grupo VID 2do intento')
	veraz_variable_1 = fields.Char('Variable 1')
	veraz_variable_2 = fields.Char('Variable 2')
	veraz_variable_3 = fields.Char('Variable 3')
	veraz_variable_4 = fields.Char('Variable 4')
	veraz_variable_5 = fields.Char('Variable 5')
	
	asignar_nombre = fields.Boolean('Asignar Nombre')
	asignar_direccion = fields.Boolean('Asignar Direccion')
	asignar_ciudad = fields.Boolean('Asignar Ciudad')
	asignar_cp = fields.Boolean('Asignar CP')
	asignar_provincia = fields.Boolean('Asignar Provincia')
	asignar_identificacion = fields.Boolean('Asignar identificacion')
	asignar_genero = fields.Boolean('Asignar genero')

	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.veraz.configuracion'))
	
	@api.one
	def test_conexion(self):
		params = {
			'usuario': self.usuario,
			'token': self.token,
		}
		response = requests.get(ENDPOINT_VERAZ, params)
		if response.status_code == 400:
			raise UserError("La cuenta esta conectada.")
		else:
			raise UserError("Error de conexion.")

class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	veraz_configuracion_id = fields.Many2one('financiera.veraz.configuracion', 'Configuracion Veraz')
