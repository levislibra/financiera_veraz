# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests
import json
import base64

ENDPOINT_VERAZ_TOKEN = "https://api.uat.latam.equifax.com/v2/oauth/token"
ENDPOINT_VERAZ_SCOPE = 'https://api.latam.equifax.com/business/integration-api-efx/v1'
ENDPOINT_VERAZ_TEST = 'https://api.uat.latam.equifax.com/business/integration-api-efx/v1/wserv'
ENDPOINT_VERAZ_PRODUCCION = 'https://api.dev.latam.equifax.com/business/integration-api-efx/v1/wserv'
# ENDPOINT_VERAZ_VID = ''

class ExtendsResPartnerVeraz(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	veraz_informe_ids = fields.One2many('financiera.veraz.informe', 'partner_id', 'Veraz - Informes')
	veraz_variable_ids = fields.One2many('financiera.veraz.informe.variable', 'partner_id', 'Variables')
	veraz_variable_1 = fields.Char('Variable 1')
	veraz_variable_2 = fields.Char('Variable 2')
	veraz_variable_3 = fields.Char('Variable 3')
	veraz_variable_4 = fields.Char('Variable 4')
	veraz_variable_5 = fields.Char('Variable 5')
	veraz_capacidad_pago_mensual = fields.Float('Veraz - CPM', digits=(16,2))
	veraz_partner_tipo_id = fields.Many2one('financiera.partner.tipo', 'Veraz - Tipo de cliente')


	pregunta_ids = fields.Char('Preguntas')


	# Validacion por cuestionario
	# veraz_cuestionario_ids = fields.One2many('financiera.veraz.cuestionario', 'partner_id', 'Veraz - Cuestionarios')
	# veraz_cuestionario_id = fields.Many2one('financiera.veraz.cuestionario', 'Veraz - Cuestionario actual')

	def get_token(self):
		print('get_token')
		veraz_configuracion_id = self.company_id.veraz_configuracion_id
		base64_string = base64.b64encode(veraz_configuracion_id.client_id + ':' + veraz_configuracion_id.client_secret)
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
		j = response.json()
		return j["access_token"]

	@api.one
	def solicitar_informe_veraz(self):
		veraz_configuracion_id = self.company_id.veraz_configuracion_id
		if veraz_configuracion_id:
			token = self.get_token()
			print("TOKEN: ", token)
			headers = {
				'Authorization': "Bearer " + token,
				'Content-Type': 'application/json'
			}
			sexo = 'B'
			if self.sexo == 'masculino':
				sexo = 'M'
			elif self.sexo == 'femenino':
				sexo = 'F'
			data = {
				"applicants": {
					"primaryConsumer": {
						"personalInformation": {
							"entity": {
								"consumer": {
									"names": [
										{
											"data": {
												"documento": str(self.dni),
												"nombre": "",
												"sexo": sexo,
											}
										}
									]
								}
							},
							"productData": {
								"sector": veraz_configuracion_id.sector,
								"billTo": veraz_configuracion_id.matriz,
								"shipTo": veraz_configuracion_id.sucursal,
								"formatReport": "T",
								"producto": "Risc:experto"
							},
							"clientConfig": {
								"clientTxId": str(self.id),
								"clientReference": "",
							},
							"variables": {},
							"globalVariables": {},
							"vinculos": []
						}
					}
				}
			}
			response = requests.post(ENDPOINT_VERAZ_TEST, json=data, headers=headers)
			data = response.json()
			# print('data', data)
			if response.status_code != 200:
				raise ValidationError("Error en la consulta de informe Veraz: "+data['description'])
			else:
				print('*************')
				list_values = []
				variables = data['applicants'][0]['SMARTS_RESPONSE']['VariablesDeSalida'].iteritems()
				print('variables: ', variables)
				for variable in variables:
					print('variable', variable)
					variable_nombre, variable_valor = variable
					variable_values = {
						'partner_id': self.id,
						'name': variable_nombre,
						'valor': variable_valor,
					}
					list_values.append((0,0, variable_values))
				nuevo_informe_id = self.env['financiera.veraz.informe'].create({})
				self.veraz_informe_ids = [nuevo_informe_id.id]
				self.veraz_variable_ids = [(6, 0, [])]
				nuevo_informe_id.write({'variable_ids': list_values})
				self.asignar_variables()
				# self.enriquecer_partner()
				if veraz_configuracion_id.asignar_direccion:
					if len(direccion) > 0:
						self.street = ' '.join(direccion)
				if veraz_configuracion_id.ejecutar_cda_al_solicitar_informe:
					nuevo_informe_id.ejecutar_cdas()

	@api.one
	def asignar_variables(self):
		variable_1 = False
		variable_2 = False
		variable_3 = False
		variable_4 = False
		variable_5 = False
		veraz_configuracion_id = self.company_id.veraz_configuracion_id
		for var_id in self.veraz_variable_ids:
			if var_id.name == veraz_configuracion_id.veraz_variable_1:
				variable_1 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == veraz_configuracion_id.veraz_variable_2:
				variable_2 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == veraz_configuracion_id.veraz_variable_3:
				variable_3 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == veraz_configuracion_id.veraz_variable_4:
				variable_4 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == veraz_configuracion_id.veraz_variable_5:
				variable_5 = var_id.name + ": " + str(var_id.valor)
		self.write({
			'veraz_variable_1': variable_1,
			'veraz_variable_2': variable_2,
			'veraz_variable_3': variable_3,
			'veraz_variable_4': variable_4,
			'veraz_variable_5': variable_5,
		})

	@api.one
	def set_provincia(self, provincia):
		if provincia == 'Capital Federal':
			provincia = 'Ciudad Autónoma de Buenos Aires'
		state_obj = self.pool.get('res.country.state')
		state_ids = state_obj.search(self.env.cr, self.env.uid, [
			('name', '=ilike', provincia)
		])
		if len(state_ids) > 0:
			self.state_id = state_ids[0]
			country_id = state_obj.browse(self.env.cr, self.env.uid, state_ids[0]).country_id
			self.country_id = country_id.id

	@api.one
	def ejecutar_cdas_veraz(self):
		if self.veraz_informe_ids and len(self.veraz_informe_ids) > 0:
			self.veraz_informe_ids[0].ejecutar_cdas()

	@api.one
	def button_solicitar_informe_veraz(self):
		self.solicitar_informe_veraz()

	# def obtener_cuestionario_veraz(self):
	# 	ret = False
	# 	veraz_configuracion_id = self.company_id.veraz_configuracion_id
	# 	grupoVid = veraz_configuracion_id.nro_grupo_vid
	# 	if len(self.veraz_cuestionario_id) > 0:
	# 		grupoVid = veraz_configuracion_id.nro_grupo_vid2
	# 	params = {
	# 		'usuario': veraz_configuracion_id.usuario,
	# 		'token': veraz_configuracion_id.token,
	# 		'NroGrupoVID': grupoVid,
	# 		'documento': self.main_id_number,
	# 		'format': 'json',
	# 	}
	# 	response = requests.get(ENDPOINT_VERAZ_VID, params)
	# 	data = response.json()
	# 	if response.status_code != 200:
	# 		raise ValidationError("Error en la obtencion del cuestionario Veraz: "+data['Contenido']['Resultado']['Novedad'])
	# 	else:
	# 		if data['Contenido']['Resultado']['Estado'] != 200:
	# 			raise ValidationError("Veraz: " + data['Contenido']['Resultado']['Novedad'])
	# 		nuevo_cuestionario_id = self.env['financiera.veraz.cuestionario'].create({})
	# 		self.veraz_cuestionario_ids = [nuevo_cuestionario_id.id]
	# 		self.veraz_cuestionario_id = nuevo_cuestionario_id.id
	# 		nuevo_cuestionario_id.id_consulta = data['Contenido']['Datos']['IdConsulta']
	# 		desafios = data['Contenido']['Datos']['Cuestionario']['Desafios']
	# 		for desafio in desafios:
	# 			if 'Pregunta' in desafio:
	# 				pregunta = desafio['Pregunta']
	# 				pregunta_id = self.env['financiera.veraz.cuestionario.pregunta'].create({
	# 					'id_pregunta': pregunta['IdPregunta'],
	# 					'texto': pregunta['Texto'],
	# 				})
	# 				nuevo_cuestionario_id.pregunta_ids = [pregunta_id.id]
	# 				i = 0
	# 				for opcion in pregunta['Opciones']:
	# 					opcion_id = self.env['financiera.veraz.cuestionario.pregunta.opcion'].create({
	# 						'id_opcion': i,
	# 						'texto': opcion,
	# 					})
	# 					i += 1
	# 					pregunta_id.opcion_ids = [opcion_id.id]
	# 		ret = nuevo_cuestionario_id.id
	# 	return ret

	# @api.one
	# def button_obtener_cuestionario_veraz(self):
	# 	self.obtener_cuestionario_veraz()

	@api.multi
	def veraz_report(self):
		self.ensure_one()
		return self.env['report'].get_action(self, 'financiera_veraz.veraz_report_view')