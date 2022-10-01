# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError, Warning
import requests
import json
import base64


ENDPOINT_VERAZ_TOKEN = "https://api.uat.latam.equifax.com/v2/oauth/token"
ENDPOINT_VERAZ_SCOPE = 'https://api.latam.equifax.com/business/integration-api-efx/v1'

ENDPOINT_VERAZ_TOKEN_IDVALIDATOR = "https://idp.equifax.com.ar/b/token?grant_type=client_credentials"

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
	id_cuestionario = fields.Char('Cuestionario ID')
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
	asignar_cuit = fields.Boolean('Asignar CUIT')
	asignar_genero = fields.Boolean('Asignar genero')

	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.veraz.configuracion'))
	
	def get_token_veraz_informes(self):
		base64_string = base64.b64encode(self.client_id + ':' + self.client_secret)
		headers = {"Authorization": "Basic " + base64_string}
		data = {
			"grant_type": "client_credentials",
			'scope': ENDPOINT_VERAZ_SCOPE,
		}
		response = requests.post(
			ENDPOINT_VERAZ_TOKEN,
			headers=headers,
			data=data,
		)
		if response.status_code != 200:
			raise UserError('Error al obtener el token de Veraz')
		j = response.json()
		return j["access_token"]

	@api.one
	def test_conexion_informes(self):
		token = self.get_token_veraz_informes()
		if token:
			raise Warning("La cuenta esta conectada. Token generado Informes: %s" % token)
		else:
			raise UserError("Error de conexion.")

	def get_token_veraz_idvalidator(self):
		base64_string = base64.b64encode(self.usuario + ':' + self.password)
		headers = {"Authorization": "Basic " + base64_string}
		data = {
			"grant_type": "client_credentials",
		}
		response = requests.post(
			ENDPOINT_VERAZ_TOKEN_IDVALIDATOR,
			headers=headers,
			json=data,
		)
		if response.status_code != 200:
			raise UserError('Error al obtener el token de Veraz: %s' % json.loads(response.text)['errorSummary'])
		j = response.json()
		return j["access_token"]

	@api.one
	def test_conexion_idvalidator(self):
		token = self.get_token_veraz_idvalidator()
		if token:
			raise Warning("La cuenta esta conectada. Token generado Id Validator: %s" % token)
		else:
			raise UserError("Error de conexion.")


