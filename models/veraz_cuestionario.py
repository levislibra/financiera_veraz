# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests

ENDPOINT_VERAZ_VID = 'https://api-idvalidator.equifax.com.ar/v1/s2s/clientID/IDCLEXP/validation/full'

class FinancieraVerazCuestionario(models.Model):
	_name = 'financiera.veraz.cuestionario'
	
	_order = 'id desc'
	name = fields.Char('Nombre')
	partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
	id_cuestionario = fields.Char('Cuestionario ID')
	name_cuestionario = fields.Char('Nombre Cuestionario')
	# indice_consulta_actual = fields.Integer('Indice consulta actual')
	pregunta_ids = fields.One2many('financiera.veraz.cuestionario.pregunta', 'cuestionario_id', 'Preguntas')
	pregunta_1_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta 1')
	pregunta_2_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta 2')
	pregunta_3_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta 3')
	pregunta_4_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta 4')
	pregunta_5_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta 5')
	pregunta_actual_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta actual', compute='_compute_pregunta_actual_id')
	# respuestas_test = fields.Char('Respuestas test')
	# cuestionario = fields.Char('Respuestas', compute='_compute_cuestionario')
	state = fields.Selection([('pendiente', 'Pendiente'), ('rechazado', 'Rechazado'), ('aprobado', 'Aprobado')], string='Estado', default='pendiente')
	state_pregunta = fields.Selection([('inicial', 'Inicial'), ('pregunta_1', 'Pregunta 1'), ('pregunta_2', 'Pregunta 2'), ('pregunta_3', 'Pregunta 3'), ('pregunta_4', 'Pregunta 4'), ('pregunta_5', 'Pregunta 5')], string='Estado pregunta', default='inicial')
	score = fields.Integer('Score')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.veraz.cuestionario'))
	
	@api.model
	def create(self, values):
		rec = super(FinancieraVerazCuestionario, self).create(values)
		rec.update({
			'name': 'VERAZ/CUESTIONARIO/' + str(rec.id).zfill(8),
		})
		return rec

	@api.one
	def obtener_preguntas(self):
		ret = False
		veraz_configuracion_id = self.company_id.veraz_configuracion_id
		headers = {
			'Authorization': 'Bearer ' + veraz_configuracion_id.get_token_veraz_idvalidator(),
			'Content-Type': 'application/json'
		}
		sexo = ''
		if self.partner_id.sexo == 'masculino':
			sexo = 'M'
		elif self.partner_id.sexo == 'femenino':
			sexo = 'F'
		params = {
			'questionnaireConfigurationId': veraz_configuracion_id.id_cuestionario,
			'documentNumber': self.partner_id.main_id_number,
			'gender': sexo,
			# 'format': 'json',
		}
		print('params', params)
		response = requests.post(
			ENDPOINT_VERAZ_VID,
			json=params,
			headers=headers)
		data = response.json()
		print('data: ', data)
		if response.status_code != 200 or ('errors' in data and data['errors']):
			raise ValidationError("Error en la obtencion del cuestionario Veraz: " + data['errors'][0]['message'])
		else:
			cuestionario = data['payload']['questionnaire']
			print('cuestionario', cuestionario)
			self.name_cuestionario = cuestionario['name']
			# print('questionnaire', cuestionario)
			for pregunta in cuestionario['questionsOfGeneratedQuestionnaire']:
				print('pregunta', pregunta)
				print('***************************')
				self.agregar_pregunta(pregunta['id'], pregunta['description'], pregunta['options'])

	@api.one
	def agregar_pregunta(self, id_pregunta, descripcion, opciones):
		vals = {
			'cuestionario_id': self.id,
			# 'opcion_ids': pregunta['question'],
			'id_pregunta': id_pregunta,
			'texto': descripcion,
		}
		pregunta_id = self.env['financiera.veraz.cuestionario.pregunta'].create(vals)
		for opcion in opciones:
			vals = {
				'pregunta_id': pregunta_id.id,
				'id_opcion': opcion['id'],
				'texto': opcion['description'],
			}
			self.env['financiera.veraz.cuestionario.pregunta.opcion'].create(vals)

	@api.one
	def iniciar_cuestionario(self):
		if self.state == 'pendiente' and self.pregunta_ids:
			if len(self.pregunta_ids) > 0:
				self.pregunta_1_id = self.pregunta_ids[0]
			if len(self.pregunta_ids) > 1:
				self.pregunta_2_id = self.pregunta_ids[1]
			if len(self.pregunta_ids) > 2:
				self.pregunta_3_id = self.pregunta_ids[2]
			if len(self.pregunta_ids) > 3:
				self.pregunta_4_id = self.pregunta_ids[3]
			if len(self.pregunta_ids) > 4:
				self.pregunta_5_id = self.pregunta_ids[4]
			self.state_pregunta = 'pregunta_1'

	@api.multi
	def ver_pregunta_actual(self):
		self.ensure_one()
		print('pregunta_actual_id', self.pregunta_actual_id)
		view_id = self.env.ref('financiera_veraz.financiera_veraz_cuestionario_pregunta_form', False)
		return {
			'name': 'Pregunta de ID Validator',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'financiera.veraz.cuestionario.pregunta',
			'res_id': self.pregunta_actual_id.id,
			'views': [(view_id.id, 'form')],
			'view_id': view_id.id,
			'target': 'new',
		}

	@api.one
	def _compute_pregunta_actual_id(self):
		self.pregunta_actual_id = False
		if self.state_pregunta == 'pregunta_1':
			self.pregunta_actual_id = self.pregunta_1_id
		elif self.state_pregunta == 'pregunta_2':
			self.pregunta_actual_id = self.pregunta_2_id
		elif self.state_pregunta == 'pregunta_3':
			self.pregunta_actual_id = self.pregunta_3_id
		elif self.state_pregunta == 'pregunta_4':
			self.pregunta_actual_id = self.pregunta_4_id
		elif self.state_pregunta == 'pregunta_5':
			self.pregunta_actual_id = self.pregunta_5_id

class FinancieraVerazCuestionarioPregunta(models.Model):
	_name = 'financiera.veraz.cuestionario.pregunta'
	
	cuestionario_id = fields.Many2one('financiera.veraz.cuestionario', 'Veraz cuestionario')
	opcion_ids = fields.One2many('financiera.veraz.cuestionario.pregunta.opcion', 'pregunta_id', 'Opciones')
	id_pregunta = fields.Integer('ID')
	texto = fields.Char('Texto')
	id_respuesta = fields.Integer('ID Respuesta', default=-1)
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.veraz.cuestionario.pregunta'))
		
class FinancieraVerazCuestionarioPreguntaOpcion(models.Model):
	_name = 'financiera.veraz.cuestionario.pregunta.opcion'
	
	pregunta_id = fields.Many2one('financiera.veraz.cuestionario.pregunta', 'Pregunta')
	id_opcion = fields.Integer('ID')
	texto = fields.Char('Texto')
	respuesta = fields.Boolean('Respuesta')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.veraz.cuestionario.pregunta.opcion'))

	@api.one
	def set_opcion_correcta(self):
		if self.pregunta_id.id_respuesta >= 0:
			self.pregunta_id.opcion_ids[self.pregunta_id.id_respuesta].respuesta = False
		self.respuesta = True
		self.pregunta_id.id_respuesta = self.id_opcion
