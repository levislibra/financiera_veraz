# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests
import json
import base64

ENDPOINT_VERAZ_TEST = 'https://api.uat.latam.equifax.com/business/integration-api-efx/v1/wserv'
ENDPOINT_VERAZ_PRODUCCION = 'https://api.dev.latam.equifax.com/business/integration-api-efx/v1/wserv'
# ENDPOINT_VERAZ_VID = ''

VARIABLES_VERAZ = {
	'nombre': 'nombre',
	'sexo': 'sexo',
	'cuit': 'xxxx',
	'direccion': 'xxxx',
	'lodalidad': 'xxxx',
	'provincia': 'xxxx',
	'cp': 'xxxx',
}

class ExtendsResPartnerVeraz(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	veraz_contratado = fields.Boolean('Veraz', compute='_compute_veraz_contrtado')
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
	veraz_cuestionario_ids = fields.One2many('financiera.veraz.cuestionario', 'partner_id', 'Veraz - Cuestionarios')
	veraz_cuestionario_id = fields.Many2one('financiera.veraz.cuestionario', 'Veraz - Cuestionario actual')

	@api.one
	def _compute_veraz_contrtado(self):
		self.veraz_contratado = True if self.company_id.veraz_configuracion_id else False

	@api.one
	def solicitar_informe_veraz(self):
		veraz_configuracion_id = self.company_id.veraz_configuracion_id
		if veraz_configuracion_id:
			token = veraz_configuracion_id.get_token_veraz_informes()
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
				self.asignar_variables_veraz()
				self.enriquecer_partner_veraz()
				if veraz_configuracion_id.ejecutar_cda_al_solicitar_informe:
					nuevo_informe_id.ejecutar_cdas()

	@api.one
	def enriquecer_partner_veraz(self):
		veraz_configuracion_id = self.company_id.veraz_configuracion_id
		vals = {}
		variable_apellido_id = False
		variable_nombre_id = False
		if veraz_configuracion_id.asignar_nombre:
			variable_nombre_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['nombre'])
			if variable_apellido_id and variable_nombre_id:
				vals['name'] = variable_nombre_id.valor
		if veraz_configuracion_id.asignar_direccion:
			variable_direccion_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['direccion'])
			if variable_direccion_id:
				vals['street'] = variable_direccion_id.valor
		if veraz_configuracion_id.asignar_ciudad:
			variable_ciudad_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['lodalidad'])
			if variable_ciudad_id:
				vals['city'] = variable_ciudad_id.valor
		if veraz_configuracion_id.asignar_cp:
			variable_cp_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['cp'])
			if variable_cp_id:
				vals['zip'] = variable_cp_id.valor
		if veraz_configuracion_id.asignar_provincia:
			variable_provincia_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['provincia'])
			if variable_provincia_id:
				self.set_provincia(variable_provincia_id.valor)
		if veraz_configuracion_id.asignar_cuit:
			variable_cuit_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['cuit'])
			if variable_cuit_id:
				vals['main_id_category_id'] = 25
				vals['main_id_number'] = variable_cuit_id.valor
		if veraz_configuracion_id.asignar_genero:
			variable_genero_id = self.veraz_variable_ids.filtered(lambda x: x.name == VARIABLES_VERAZ['sexo'])
			if variable_genero_id:
				if variable_genero_id.valor == 'M':
					vals['sexo'] = 'masculino'
				elif variable_genero_id.valor == 'F':
					vals['sexo'] = 'femenino'
		self.write(vals)

	@api.one
	def asignar_variables_veraz(self):
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

	def obtener_cuestionario_veraz(self):
		cuestionario_id = self.env['financiera.veraz.cuestionario'].create({'partner_id': self.id})
		self.veraz_cuestionario_id = cuestionario_id.id
		cuestionario_id.obtener_preguntas()
		return cuestionario_id

	@api.one
	def button_obtener_cuestionario_veraz(self):
		self.obtener_cuestionario_veraz()

	@api.multi
	def ver_cuestionario_actual(self):
		self.ensure_one()
		view_id = self.env.ref('financiera_veraz.financiera_veraz_cuestionario_form', False)
		return {
			'name': 'Pregunta de ID Validator',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'financiera.veraz.cuestionario',
			'res_id': self.veraz_cuestionario_id.id,
			'views': [(view_id.id, 'form')],
			'view_id': view_id.id,
			'target': 'new',
		}

	@api.multi
	def veraz_report(self):
		self.ensure_one()
		return self.env['report'].get_action(self, 'financiera_veraz.veraz_report_view')