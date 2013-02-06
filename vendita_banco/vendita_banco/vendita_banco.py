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

from osv import fields, osv
from tools.translate import _
import datetime
import time
import decimal_precision as dp


class vendita_banco_trasporto(osv.osv):

	_name = "vendita_banco.trasporto"
	_description = "Lista Tipologie Trasporto"

	_columns = {
		'name' : fields.char('Descrizione', size=64),
		}

vendita_banco_trasporto()


class vendita_banco(osv.osv):

	_name = "vendita_banco"
	_description = "Vendite"

	def copy(self, cr, uid, id, default={}, context=None):
		default.update({'name': '', 'invoice_id':False})
		return super(vendita_banco, self).copy(cr, uid, id, default, context)
		
	def unlink(self, cr, uid, ids, context=None):
		for vendita in self.browse(cr, uid, ids):
			if vendita.state != 'draft':
				raise osv.except_osv(_('Azione non valida!'), _('Impossibile eliminare una vendita validata!'))
				return False
			else:
				if not vendita.causale.fattura and vendita.name:
					vendita.causale.recupera_protocollo(vendita.name, vendita.data_ordine)
				return super(vendita_banco, self).unlink(cr, uid, vendita.id, context)

	def create(self, cr, uid, vals, context=None):
		vals.update({'user_id':uid})
		return super(vendita_banco,self).create(cr, uid, vals, context=context)

	# ----- calcola gli importi per ogni riga dell'ordine
	def _calcola_importi(self, cr, uid, ids, field_name, arg, context=None):
		# ----- Calcola il totale della riga di dettaglio
		res = {}
		for vb in self.browse(cr, uid, ids, context):
			res[vb.id] = {'totale':0.0, 'imponibile':0.0,}
			for line in vb.vendita_banco_dettaglio_ids:
				res[vb.id]['totale'] += (line.importo * int(vb.causale.segno))
				res[vb.id]['imponibile'] += (line.imponibile * int(vb.causale.segno))
		return res

	# ----- restituisce true se la causale ha un report in modo da mostrare il button sdi stampa 
	def _get_report(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		vbs = self.browse(cr, uid, ids, context)
		for vb in vbs:
			if vb.causale.report:
				res[vb.id] = True
			else:
				res[vb.id] = False
		return res
		
	def _get_company(self, cr, uid, ids, name, arg, context=None):
		res = {}
		vbs = self.browse(cr, uid, ids, context)
		company_id = self.pool.get('res.company')._company_default_get(cr, uid, context=context)
		if not company_id:
			for vb in vbs:
				res[vb.id] = False
		else:
			for vb in vbs:
				res[vb.id] = company_id
		return res

	_columns = {
		'name' : fields.char('Numero Documento', size=16),
		'user_id': fields.many2one('res.users','Utente'),
		'data_ordine' : fields.date('Data Ordine', required=True),
		'partner_id' : fields.many2one('res.partner', 'Cliente', required=True),
		'partner_invoice_id' : fields.many2one('res.partner.address', 'Indirizzo Fatturazione', required=True),
		'partner_shipping_id' : fields.many2one('res.partner.address', 'Indirizzo Spedizione'),
		'pricelist_id' : fields.many2one('product.pricelist', 'Listino Prezzi', required=True),
		'ddt' : fields.related('causale', 'ddt', type='boolean', relation='vendita.causali', readonly=True, help="Se la casella è spuntata verrà generato e stampato un DDT altrimenti verrà creato un altro documento"),
		'fatturabile' : fields.related('causale', 'fatturabile', type='boolean', relation='vendita.causali', readonly=True),
		'report' : fields.function(_get_report,  method=True, type='boolean'),
		'company_id' : fields.function(_get_company,  method=True, type='many2one', relation='res.company', store=False),
		'causale' : fields.many2one('vendita.causali', 'Causale', required=True),
		'invoice_id' : fields.many2one('account.invoice', 'Fattura', ondelete='set null'),
		'modalita_pagamento_id' : fields.many2one('account.payment.term', 'Modalità di pagamento', required=True),
		# ----- Campi di gestione ddt
		'goods_description_id' : fields.many2one('stock.picking.goods_description','Aspetto dei beni'),
		'carriage_condition_id' : fields.many2one('stock.picking.carriage_condition','Resa merce'),
		'transportation_reason_id' : fields.many2one('stock.picking.transportation_reason','Causale Trasporto'),
		'number_of_packages' : fields.integer('Numero Colli'),
		'trasportatore_id' : fields.many2one('delivery.carrier', 'Trasportatore'),
		'tipo_trasporto_id' : fields.many2one('vendita_banco.trasporto', 'Tipo Trasporto'),
		'data_inizio_trasporto' : fields.datetime('Data Inizio Trasporto'),
		# ----- Dettagli
		'vendita_banco_dettaglio_ids' : fields.one2many('vendita_banco.dettaglio', 'vendita_banco_id', 'Dettagli', ondelete='cascade', readonly=True, states={'draft': [('readonly', False)]}),
		'totale' : fields.function(_calcola_importi, method=True, 
			digits_compute=dp.get_precision('Account'),
			string='Totale', type='float', store=True, multi='sums'),
		'imponibile' : fields.function(_calcola_importi, method=True,
			digits_compute=dp.get_precision('Account'),
			string='Totale Imponibile', type='float', store=True, multi='sums'),
		'acconto' : fields.float('Acconto', digits_compute=dp.get_precision('Account')),
		'state' : fields.selection((('draft', 'Preventivo'),('done', 'Confermato'), ('invoiced', 'Fatturato')), 'Stato', readonly=True, select=True),
		# ----- Altro
		'note' : fields.text('Note'),
		# ----- Wizard
		# --- Contiene l'id di un eventuale ordine generato da raggruppamento con wizard
		'vb_raggruppamento_id' : fields.many2one('vendita_banco', 'Ordine Raggruppamento', ondelete="set null"),
		}

	_defaults = {
		'state' : 'draft',
		'name' : '',
		'data_ordine': lambda *a: time.strftime('%Y-%m-%d'),
		'data_inizio_trasporto': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
	}
	
	_order = "data_ordine desc, name desc"

	# ----- Funzione che aggiorna il flag ddt
	def onchange_causale(self, cr, uid, ids, causale):
		if causale:
			causale_vals = self.pool.get('vendita.causali').browse(cr,uid,causale)
			warning = {}
			if not self.pool.get('res.users').browse(cr, uid, uid) in causale_vals.user_ids:
				warning = {
					'title' : 'Attenzione!',
					'message' : 'Non si è abilitati all\'emissione di una vendita con questa causale!'
					}
				causale = False
			ddt = causale_vals.ddt
			return {'value' : {'ddt' : ddt, 'name':'', 'causale':causale}, 'warning': warning}
		return False
	
	# ----- Funzione che oltre al normale onchange inserisce anche il valore di genera ddt del partner
	def onchange_cliente_id(self, cr, uid, ids, part, causale):
		if not part:
			return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'payment_term': False, 'fiscal_position': False}}
		addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['delivery', 'invoice'])
		part = self.pool.get('res.partner').browse(cr, uid, part)
		pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
		val = {
			'partner_invoice_id': addr['invoice'],
			'partner_shipping_id': addr['delivery'],
			'causale' : causale or part.causale and part.causale.id or False,
			'ddt' : causale and self.pool.get('vendita.causali').browse(cr,uid,causale).ddt or False,
			'goods_description_id' : part.goods_description_id and part.goods_description_id.id or False,
			'carriage_condition_id' : part.carriage_condition_id and part.carriage_condition_id.id or False,
			'modalita_pagamento_id' : part.property_payment_term and part.property_payment_term.id or False,
			'transportation_reason_id' : part.transportation_reason_id and part.transportation_reason_id.id or False,
			'tipo_trasporto_id' : part.tipo_trasporto_id and part.tipo_trasporto_id.id or False,
		}
		if pricelist:
			val['pricelist_id'] = pricelist
		return {'value': val}

	
	def onchange_modalita_pagamento(self, cr, uid, ids, modalita_pagamento_id):
		val = {}
		if not modalita_pagamento_id:
			return {'value': val}
		'''
		val = {'vendita_banco_dettaglio_ids':[]}
		mod_pag_obj = self.pool.get('account.payment.term')
		modalita_pagamento = mod_pag_obj.browse(cr, uid, modalita_pagamento_id)
		for line in modalita_pagamento.line_ids:
			if line.spesa_id:
				val['vendita_banco_dettaglio_ids'] += [(0, 0, {
					'spesa':True,
					'name':line.spesa_id.name,
					'price_unit':line.spesa_id.price,
					'tax_id':line.spesa_id.tax_id and line.spesa_id.tax_id.id,
					'product_qty' : 1,
					})]
		print '============', val
		'''
		return {'value': val}
	

	# ----- Funzione richiamata dal button Conferma Vendita
	def conferma_vendita(self, cr, uid, ids, *args):
		order_objs = self.browse(cr, uid, ids)
		warehouse_obj = self.pool.get('stock.warehouse')
		warehouse_id = warehouse_obj.search(cr, uid, [('id', '>', 0)])[0]
		warehouse = warehouse_obj.browse(cr, uid, warehouse_id)
		for order_obj in order_objs:
			if order_obj.causale.tipo in ['carico', 'scarico']:	# se non è un carico/scarico non fa nulla
				if not order_obj.vendita_banco_dettaglio_ids:
					raise osv.except_osv(_('Azione non valida!'), _('Non esistono righe di vendita per questo ordine!'))
					return False
				# ----- CREA UN MOVIMENTO DI MAGAZZINO PER OGNI RIGA DI VENDITA
				# imposta il verso della merce
				if order_obj.causale.tipo == 'scarico':
					location_sorgente = warehouse.lot_stock_id.id
					location_destinazione = order_obj.causale.location_id and order_obj.causale.location_id.id or warehouse.location_vendita_banco_id.id
				else:
					location_destinazione = order_obj.causale.location_id and order_obj.causale.location_id.id or warehouse.lot_stock_id.id
					location_sorgente = warehouse.location_vendita_banco_id.id
				for line in order_obj.vendita_banco_dettaglio_ids:
					if line.product_id and line.product_id.type != 'service':
						move_obj = self.pool.get('stock.move')
						move_valori = {
							'name' : '[%s] %s' % (line.product_id.default_code, line.product_id.name),
							'sorgente_id' : line.vendita_banco_id.id,
							'product_uom' : line.product_uom.id,
							'price_unit' : line.price_unit,
							'product_qty' : line.product_qty,
							'product_id' : line.product_id.id,
							'location_id' : location_sorgente,
							'location_dest_id' :location_destinazione,
							'state' : 'done',
						}
						move_id = move_obj.create(cr, uid, move_valori)
						self.pool.get('vendita_banco.dettaglio').write(cr, uid, line.id, {'move_id':move_id})
			# ----- INSERISCE EVENTUALI LINEE DI SPESA
			for line in order_obj.modalita_pagamento_id.line_ids:
				if line.spesa_id:
					vals = {
						'spesa':True,
						'name':line.spesa_id.name,
						'price_unit':line.spesa_id.price,
						'tax_id':line.spesa_id.tax_id and line.spesa_id.tax_id.id,
						'product_qty' : 1,
						'vendita_banco_id' : order_obj.id,
						}
					self.pool.get('vendita_banco.dettaglio').create(cr, uid, vals)
			# ----- SCRIVE IL NUMERO DI PROTOCOLLO NUOVO O LO RECUPERA
			res = {}
			res['name'] = order_obj.name or order_obj.causale.get_protocollo()
			# ----- SCRIVE LO STATO
			res['state'] = 'done'
			self.write(cr, uid, order_obj.id, res)
			if order_obj.causale.fattura:
				return self.crea_fatture_raggruppate(cr, uid, ids, order_obj.data_ordine, order_obj.causale.name, args[0])
		return True

	def crea_fatture_raggruppate(self, cr, uid, ids, data_fattura, origin, context):
		order_objs = self.browse(cr, uid, ids)
		journal_ids = self.pool.get('account.journal').search(cr, uid, [('type','=','sale')])
		journal_id = journal_ids[0]
		account_id = self.pool.get('account.account').search(cr, uid, [('code', '=', '310100')])[0]
		currency_id = False
		currency_ids = self.pool.get('res.currency').search(cr, uid, [('name', '=', 'EUR')])
		if currency_ids:
			currency_id = currency_ids[0]
		# -----
		# CREAZIONE
		# -----
		for order_obj in order_objs:
			# -----
			# CREAZIONE TESTATA FATTURA
			# -----
			account_invoice_id = self.pool.get('account.invoice').create(cr, uid, {
				'name' : order_obj.causale.fattura and order_obj.causale.descrizione or "Fattura Differita",
				'origin' : order_obj.name,
				'date_invoice' : data_fattura,
				'immediate' : order_obj.causale.fattura,
				'partner_id' : order_obj.partner_id.id,
				'account_id' : order_obj.partner_id.property_account_receivable.id,
				'journal_id' : journal_id,
				'currency_id' : currency_id,
				'address_invoice_id' : order_obj.partner_invoice_id.id,
				'partner_shipping_id' : order_obj.partner_shipping_id and order_obj.partner_shipping_id.id,
				'state' : 'draft',
				'type' : 'out_invoice',
				'reconciled' : False,
				'fiscal_position' : order_obj.partner_id.property_account_position.id,
				'payment_term' : order_obj.modalita_pagamento_id.id,
				'journal_id' : order_obj.causale and order_obj.causale.journal_id and order_obj.causale.journal_id.id or False,
				'comment' : order_obj.note,
				'carriage_condition_id' : order_obj.carriage_condition_id and order_obj.carriage_condition_id.id or False,
				'goods_description_id' : order_obj.goods_description_id and order_obj.goods_description_id.id or False,
				'transportation_reason_id' : order_obj.transportation_reason_id and order_obj.transportation_reason_id.id or False,
				'packages_number' : order_obj.number_of_packages or 0.0,
				})
			# CREA UNA RIGA FITTIZIA COME TESTATA
			if order_obj.causale.riga_raggruppa:
				invoice_fake_line_id = self.pool.get('account.invoice.line').create(cr, uid, {
						'name' : 'Rif. Vs. Doc. Nr. %s' % (order_obj.name,),
						'invoice_id' : account_invoice_id,
						'quantity' : 1,
						'account_id' : account_id,
						'price_unit' : 0.0,
						})
			# ----- CREA LE RIGHE REALI DEI PRODOTTI
			for line in order_obj.vendita_banco_dettaglio_ids:
				invoice_line_tax_id = line.tax_id and [(6,0,[line.tax_id.id])] or False
				invoice_line_id = self.pool.get('account.invoice.line').create(cr, uid, {
					'name' : line.name,
					'invoice_id' : account_invoice_id,
					'product_id' : line.product_id and line.product_id.id or False,
					'quantity' : line.product_qty,
					'account_id' : account_id,
					'price_unit' : line.price_unit,
					'discount' : line.discount,
					'partner_id' : line.vendita_banco_id.partner_id.id,
					'invoice_line_tax_id' : invoice_line_tax_id,
					'uos_id' : line.product_uom.id,
					})
				self.pool.get('vendita_banco.dettaglio').write(cr, uid, [line.id], {'invoice_line_id':invoice_line_id})
		# ----- Salva in vendita_banco la fattura appena creata e modifica lo stato
		self.write(cr, uid, ids, {'invoice_id':account_invoice_id, 'state':'invoiced'})
		# ----- MOSTRA LA FATTURA APPENA CREATA
		mod_obj = self.pool.get('ir.model.data')
		res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
		res_id = res and res[1] or False,
		return {
			'name': 'Customer Invoices',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': [res_id],
			'res_model': 'account.invoice',
			'context': "{'type':'out_invoice'}",
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': account_invoice_id or False,
		}

	# ----- Funzione che crea la fattura dal button nel form
	def crea_fattura(self, cr, uid, ids, *args):
		data_fattura = datetime.datetime.today()
		data_fattura = '%s/%s/%s' % (data_fattura.strftime('%d'), data_fattura.strftime('%m'), data_fattura.strftime('%Y'))
		origin = self.browse(cr, uid, ids[0]).name
		return self.crea_fatture_raggruppate(cr, uid, ids, data_fattura, origin, args[0])

	# ----- Funzione richiamata dal button Conferma Vendita
	def riapri_vendita(self, cr, uid, ids, *args):
		for order_obj in self.browse(cr, uid, ids):
			move_obj = self.pool.get('stock.move')
			# ----- Controlla che non ci siano fatture generate da questi ordini
			if (order_obj.state == 'invoiced') and (order_obj.invoice_id):
				message = 'La fattura "%s" e\' collegata a questo ordine\nAccertarsi che essa venga eliminata prima di procedere!' % (order_obj.invoice_id.number or order_obj.invoice_id.name)
				raise osv.except_osv(_('Attenzione!'), _(message))
				return False
			# ----- Controlla che non ci siano ordini di raggruppamento generati da questi ordini
			if order_obj.vb_raggruppamento_id:
				message = 'L\'ordine di raggruppamento "%s" e\' collegata a questo ordine\nAccertarsi che essa venga eliminata prima di procedere!' % (order_obj.vb_raggruppamento_id.name)
				raise osv.except_osv(_('Attenzione!'), _(message))
				return False
			# ----- Cancello i movimenti collegati
			for line in order_obj.vendita_banco_dettaglio_ids:
				if line.move_id and move_obj.browse(cr,uid,line.move_id):
					move_obj.write(cr, uid, [line.move_id.id], {'state':'draft'})
					move_obj.unlink(cr, uid, [line.move_id.id])
				if line.spesa:
					self.pool.get('vendita_banco.dettaglio').unlink(cr, uid, [line.id,])
		# ----- Cambio lo stato
		res = {}
		res['state'] = 'draft'
		self.write(cr, uid, ids, res)
		return True

	# ----- Funzione richiamata dal button Stampa BC o DDT
	def stampa(self, cr, uid, ids, context=None):
		order_obj = self.browse(cr, uid, ids[0])
		report_name = order_obj.causale.report.report_name
		return {
			# ----- Jasper Report
			'type':'ir.actions.report.xml',
			'report_name': report_name,
			'datas': {
				'model':'vendita_banco',
				'ids': ids,
				'report_type': 'pdf',
			},
			'nodestroy': True,
		}

vendita_banco()


class vendita_banco_dettaglio(osv.osv):

	_name = "vendita_banco.dettaglio"
	_description = "Vendite"

	# ----- calcola gli importi per ogni riga dell'ordine
	def _calcola_importi(self, cr, uid, ids, field_name, arg, context=None):
		# ----- Calcola il totale della riga di dettaglio
		res = {}
		for line in self.browse(cr, uid, ids, context):
			res[line.id] = {'importo':0.0, 'imponibile':0.0,}
			imponibile = line.price_unit * line.product_qty
			# ----- applica lo sconto
			if line.discount:
				#sconto = imponibile * line.discount
				#imponibile = imponibile - sconto
				imponibile = imponibile * ( 1 - (line.discount / 100.00))
			tax_amount = line.tax_id and line.tax_id.amount or 0
			importo = (imponibile * tax_amount) + imponibile
			res[line.id]['importo'] = importo
			res[line.id]['imponibile'] = imponibile
		return res

	_columns = {
		'name' : fields.char('Descrizione', size=64),
		'vendita_banco_id' : fields.many2one('vendita_banco', 'Vendita', ondelete='cascade'),
		'partner_id' : fields.related('vendita_banco_id', 'partner_id', string="Cliente", type="many2one", relation="res.partner", store=True),
		'causale' : fields.related('vendita_banco_id', 'causale', string="Causale", type="many2one", relation="vendita.causali", store=True),
		'product_id' : fields.many2one('product.product', 'Prodotto'),
		'product_qty' : fields.float('Quantità'),
		'product_uom' : fields.many2one('product.uom', 'Unità di misura'),
		'price_unit' : fields.float('Prezzo Unitario', digits_compute=dp.get_precision('Vendita Banco Dettaglio')),
		'discount' : fields.float('Sconto (%)', help="Indicare uno sconto in percentuale"),
		'tax_id': fields.many2one('account.tax', 'IVA'),
		'importo' : fields.function(_calcola_importi, method=True, digits_compute=dp.get_precision('Vendita Banco Dettaglio'), 
			string='Importo', type='float', store=False, multi='sums'),
		'imponibile' : fields.function(_calcola_importi, method=True, digits_compute=dp.get_precision('Vendita Banco Dettaglio'),
			string='Imponibile', type='float', store=False, multi='sums'),
		'move_id' : fields.many2one('stock.move', 'Movimento'),
		'invoice_line_id' : fields.many2one('account.invoice.line', 'Linea di fattura'),
		'spesa' : fields.boolean('Spesa'),
	}

	def onchange_product(self, cr, uid, ids, product_id, product_qty, data_ordine, partner_id, pricelist, tax_id=False, context={}):
		if product_id:
			res = {}
			product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
			# ----- Aggiunge eventuale IVA presente nel prodotto
			if (not tax_id) and (product_obj.taxes_id):
				res['tax_id'] = product_obj.taxes_id[0].id
			warning = {}
			res['product_uom'] = product_obj.uom_id.id
			res['product_qty'] = 1
			res['name'] = '%s' % (product_obj.name)
			# ----- richiama lo sconto fisso
			if partner_id:
				res['discount'] = self.pool.get('res.partner').browse(cr, uid, partner_id).sconto_fisso
			if not pricelist:
				warning = {
					'title' : 'Nessun Listino!',
					'message' : 'Selezionare un listino di vendita o associarne uno al cliente!'
					}
			else:
				price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
						product_id, product_qty or 1.0, partner_id, {
							'uom': product_obj.uom_id.id,
							'date': data_ordine,
							})[pricelist]
				if price is False:
					warning = {
						'title' : 'Nessuna linea del listino valida trovata!',
						'message' : 'Impossibile trovare una linea del listino valida per questo prodotto.'
						}
				else:
					res['price_unit'] = price
			return {'value':res, 'warning': warning}
		return False

vendita_banco_dettaglio()
