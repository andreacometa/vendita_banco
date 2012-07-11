# -*- encoding: utf-8 -*-
##############################################################################
#
#    Personalizzazione realizzata da Francesco OpenCode Apruzzese
#    Compatible with OpenERP release 6.0.0
#    Copyright (C) 2010 Andrea Cometa. All Rights Reserved.
#    Email: cescoap@gmail.com
#    Web site: http://www.andreacometa.it
#
##############################################################################


from osv import fields,osv
from tools.translate import _


class vb_modifica_causale(osv.osv_memory):

	_name = "vb.modifica_causale"
	_description = "Modifica la causale su doc confermati"

	_columns = {
		'nuova_causale' : fields.many2one('vendita.causali', 'Causale', required=True),
		# ----- Dati DDT
		'ddt' : fields.boolean('DDT'),
		'goods_description_id' : fields.many2one('stock.picking.goods_description','Aspetto dei beni'),
		'carriage_condition_id' : fields.many2one('stock.picking.carriage_condition','Resa merce'),
		'transportation_reason_id' : fields.many2one('stock.picking.transportation_reason','Causale Trasporto'),
		'number_of_packages' : fields.integer('Numero Colli'),
		'trasportatore_id' : fields.many2one('delivery.carrier', 'Trasportatore'),
		}

	def onchange_causale(self, cr, uid, ids, causale, context):
		if causale and self.pool.get('vendita.causali').browse(cr,uid,causale).ddt:
			vb = self.pool.get('vendita_banco').browse(cr, uid, context['active_id'])
			return {'value' : {'goods_description_id' : vb.partner_id.goods_description_id and vb.partner_id.goods_description_id.id or False,
				'transportation_reason_id' : vb.partner_id.transportation_reason_id and vb.partner_id.transportation_reason_id.id or False ,
				'carriage_condition_id': vb.partner_id.transportation_reason_id and vb.partner_id.transportation_reason_id.id or False,
				'ddt' : True,}}
		else:
			return {'value' : {'goods_description_id' : False,
				'transportation_reason_id' : False ,
				'carriage_condition_id': False,
				'ddt': False,}}

	def modifica_causale(self, cr, uid, ids, context={}):
		if 'active_id' in context:
			wizard = self.browse(cr, uid, ids[0])
			vb_obj = self.pool.get('vendita_banco')
			vb = vb_obj.browse(cr, uid, context['active_id'])
			if vb.state == 'draft':
				raise osv.except_osv(_('Attenzione!'), _('Questa procedura è applicabile solo agli ordini confermati!'))
			# ----- recuperiamo il protocollo
			if not (vb.causale.fattura or vb.causale.fatturabile):
				vb.causale.recupera_protocollo(vb.name, vb.data_ordine)
			# ----- Generiamo un nuovo protocollo
			nuovo_protocollo = wizard.nuova_causale.get_protocollo()
			values = {'name':nuovo_protocollo,
				'causale':wizard.nuova_causale.id,
				'goods_description_id':False,
				'carriage_condition_id':False,
				'transportation_reason_id':False,
				'number_of_packages':0,
				'trasportatore_id':False,
				'ddt':False,
				}
			if wizard.nuova_causale.ddt:
				values['ddt'] = True
				values['goods_description_id'] = wizard.goods_description_id.id
				values['carriage_condition_id'] = wizard.carriage_condition_id.id
				values['transportation_reason_id'] = wizard.transportation_reason_id.id
				values['number_of_packages'] = wizard.number_of_packages
				values['trasportatore_id'] = wizard.trasportatore_id and wizard.trasportatore_id.id or False
			vb_obj.write(cr, uid, [vb.id,], values)
		return {'type': 'ir.actions.act_window_close'}

vb_modifica_causale()
