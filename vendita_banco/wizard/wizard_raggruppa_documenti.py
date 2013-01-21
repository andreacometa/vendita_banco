# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Andrea Cometa All Rights Reserved.
#                       www.andreacometa.it
#                       openerp@andreacometa.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields,osv
from tools.translate import _


class vb_raggruppa_documenti(osv.osv_memory):

	_name = "vb.raggruppa_documenti"
	_description = "Raggruppa documenti in un nuovo ordine con diversa causale"

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

	def raggruppa_crea(self, cr, uid, ids, context={}):
		if 'active_ids' in context:
			wizard = self.browse(cr, uid, ids[0])
			vb_obj = self.pool.get('vendita_banco')
			vb_lines_obj = self.pool.get('vendita_banco.dettaglio')
			vbs = vb_obj.browse(cr, uid, context['active_ids'])
			# ----- Controlla che tutti i documenti siano confermati
			for vb in vbs:
				if vb.state == 'draft':
					raise osv.except_osv(_('Attenzione!'), _('Questa procedura è applicabile solo agli ordini confermati!'))
				if not wizard.nuova_causale in vb.causale.raggruppamento_ids:
					raise osv.except_osv(_('Attenzione!'), _('La causale di uno dei movimento non permette il raggruppamento come %s!' % (wizard.nuova_causale.name)))
			# ----- Genera la testa del nuovo documento
			vb_struttura = {
				'partner_id' : vbs[0].partner_id.id,
				'partner_invoice_id' : vbs[0].partner_invoice_id.id,
				'partner_shipping_id' : vbs[0].partner_shipping_id.id,
				'pricelist_id' : vbs[0].pricelist_id.id,
				'modalita_pagamento_id' : vbs[0].modalita_pagamento_id.id,
				'causale' : wizard.nuova_causale.id,
				'goods_description_id' : wizard.goods_description_id.id,
				'carriage_condition_id' : wizard.carriage_condition_id.id,
				'transportation_reason_id' : wizard.transportation_reason_id.id,
				'number_of_packages' : wizard.number_of_packages,
				'trasportatore_id' : wizard.trasportatore_id.id,
			}
			nuovo_vb_id = vb_obj.create(cr, uid, vb_struttura)
			# ----- Indica il nuovo ordine in quelli vecchi
			vb_obj.write(cr, uid, context['active_ids'], {'vb_raggruppamento_id':nuovo_vb_id})
			# ----- Genera i dettagli del nuovo documento
			for vb in vbs:
				# ----- Crea la riga descrittiva di riferimento
				vb_line_struttura = {
					'name' : 'Riferimento: %s' % (vb.name,),
					'vendita_banco_id' : nuovo_vb_id,
					'product_id' : False,
					'product_uom' : False,
					'product_qty' : 0.0,
					'price_unit' : 0.0,
					'tax_id' : False,
				}
				vb_lines_obj.create(cr, uid, vb_line_struttura)
				for line in vb.vendita_banco_dettaglio_ids:
					# ----- Crea la righe dei prodotti
					vb_line_struttura = {
						'name' : line.name,
						'vendita_banco_id' : nuovo_vb_id,
						'product_id' : line.product_id.id,
						'product_uom' : line.product_uom.id,
						'product_qty' : line.product_qty,
						'price_unit' : line.price_unit,
						'tax_id' : line.tax_id and line.tax_id.id,
						'discount' : line.discount,
					}
					vb_lines_obj.create(cr, uid, vb_line_struttura)
			# ----- Mostra il documento appena creato
			mod_obj = self.pool.get('ir.model.data')
			res = mod_obj.get_object_reference(cr, uid, 'vendita_banco', 'view_vendita_banco_form')
			res_id = res and res[1] or False,
			return {
				'name': 'Vendita Banco',
				'view_type': 'form',
				'view_mode': 'form',
				'view_id': [res_id],
				'res_model': 'vendita_banco',
				'type': 'ir.actions.act_window',
				#'nodestroy': True,
				'target': 'current',
				'res_id': nuovo_vb_id or False,
			}
		return {'type': 'ir.actions.act_window_close'}

vb_raggruppa_documenti()
