# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError, Warning
import requests
import json
import base64

# ENDPOINT_VERAZ_TOKEN_TEST = "https://api.uat.latam.equifax.com/v2/oauth/token"
# ENDPOINT_VERAZ_TOKEN_PRODUCCION = "https://api.latam.equifax.com/v2/oauth/token"
ENDPOINT_VERAZ_TOKEN_TEST = "https://interconnect-uat.7x24.com.ar/token"
ENDPOINT_VERAZ_TOKEN_PRODUCCION = "https://interconnect-prd.7x24.com.ar/token"

ENDPOINT_VERAZ_SCOPE = 'https://api.latam.equifax.com/business/integration-api-efx/v1'

# ENDPOINT_VERAZ_TOKEN_IDVALIDATOR = "https://idp.equifax.com.ar/b/token?grant_type=client_credentials"
IDVALIDATOR_ENDPOINT_VERAZ_TOKEN_TEST = "https://id3-uat.7x24.com.ar/IDToken"
IDVALIDATOR_ENDPOINT_VERAZ_TOKEN_PRODUCCION = "https://id3-prd.7x24.com.ar/IDToken"

IDVALIDATOR_ENDPOINT_VERAZ_SCOPE = 'https://api.latam.equifax.com/ifctribe-idv'

class FinancieraVerazConfiguracion(models.Model):
	_name = 'financiera.veraz.configuracion'

	name = fields.Char('Nombre')
	state = fields.Selection([('test','Test'),('produccion','Produccion')], string='Estado', default='test')
	client_id_test = fields.Char('Cliente ID Test')
	client_secret_test = fields.Char('Cliente Secret Test')
	client_id = fields.Char('Cliente ID')
	client_secret = fields.Char('Cliente Secret')
	# ID Validator
	idvalidator_client_id_test = fields.Char('ID Validator - Cliente ID Test')
	idvalidator_client_secret_test = fields.Char('ID Validator - Cliente Secret Test')
	idvalidator_client_id = fields.Char('ID Validator - Cliente ID')
	idvalidator_client_secret = fields.Char('ID Validator - Cliente Secret')
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
	
	@api.one
	def change_state(self):
		self.state = 'produccion' if self.state == 'test' else 'test'

	def get_token_veraz_informes(self):
		client_id = self.client_id_test if self.state == 'test' else self.client_id
		client_secret = self.client_secret_test if self.state == 'test' else self.client_secret
		base64_string = base64.b64encode(client_id + ':' + client_secret)
		headers = {"Authorization": "Basic " + base64_string}
		data = {
			"grant_type": "client_credentials",
			'scope': ENDPOINT_VERAZ_SCOPE,
		}
		endpoint_veraz_token = ENDPOINT_VERAZ_TOKEN_PRODUCCION if self.state == 'produccion' else ENDPOINT_VERAZ_TOKEN_TEST
		response = requests.post(
			endpoint_veraz_token,
			headers=headers,
			data=data,
		)
		print("response: ", response)
		print("response.text: ", response.text)
		if response.status_code != 200:
			raise UserError('Error al obtener el token de Veraz :(')
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
		print("get_token_veraz_idvalidator")
		client_id = self.idvalidator_client_id_test if self.state == 'test' else self.idvalidator_client_id
		client_secret = self.idvalidator_client_secret_test if self.state == 'test' else self.idvalidator_client_secret
		print("client_id: ", client_id)
		print("client_secret: ", client_secret)
		base64_string = base64.b64encode(client_id + ':' + client_secret)
		headers = {"Authorization": "Basic " + base64_string}
		data = {
			"grant_type": "client_credentials",
			'scope': IDVALIDATOR_ENDPOINT_VERAZ_SCOPE,
		}
		idvalidator_endpoint_veraz_token = IDVALIDATOR_ENDPOINT_VERAZ_TOKEN_PRODUCCION if self.state == 'produccion' else IDVALIDATOR_ENDPOINT_VERAZ_TOKEN_TEST
		print("idvalidator_endpoint_veraz_token: ", idvalidator_endpoint_veraz_token)
		response = requests.post(
			idvalidator_endpoint_veraz_token,
			headers=headers,
			json=data,
		)
		print("response: ", response)
		print("response.text: ", response.text)
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


