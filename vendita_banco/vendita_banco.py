# -*- encoding: utf-8 -*-
##############################################################################
#
#    Personalizzazione realizzata da Andrea Cometa
#    Compatible with OpenERP release 6.0.0
#    Copyright (C) 2010 Andrea Cometa. All Rights Reserved.
#    Email: info@andreacometa.it
#    Web site: http://www.andreacometa.it
#
##############################################################################

from osv import fields, osv
from tools.translate import _
import datetime
import time

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
		'data_ordine' : fields.date('Data Ordine', required=True),
		'partner_id' : fields.many2one('res.partner', 'Cliente', required=True),
		'partner_invoice_id' : fields.many2one('res.partner.address', 'Indirizzo Fatturazione', required=True),
		'partner_shipping_id' : fields.many2one('res.partner.address', 'Indirizzo Spedizione'),
		'pricelist_id' : fields.many2one('product.pricelist', 'Listino Prezzi', required=True),
		'ddt' : fields.boolean('DDT', help="Se la casella è spuntata verrà generato e stampato un DDT altrimenti verrà crerato un Buono Consegna"),
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
		# ----- Dettagli
		'vendita_banco_dettaglio_ids' : fields.one2many('vendita_banco.dettaglio', 'vendita_banco_id', 'Dettagli', ondelete='cascade', readonly=True, states={'draft': [('readonly', False)]}),
		'totale' : fields.function(_calcola_importi, method=True, string='Totale', type='float', store=True, multi='sums'),
		'imponibile' : fields.function(_calcola_importi, method=True, string='Totale Imponibile', type='float', store=True, multi='sums'),
		'acconto' : fields.float('Acconto'),
		'state' : fields.selection((('draft', 'Preventivo'),('done', 'Confermato'), ('invoiced', 'Fatturato')), 'Stato', readonly=True, select=True),
		# ----- Altro
		'note' : fields.text('Note'),
		}

	_defaults = {
		'state' : 'draft',
		'name' : '',
		'data_ordine': lambda *a: time.strftime('%Y-%m-%d'),
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
			'causale' : part.causale and part.causale.id or causale,
			'goods_description_id' : part.goods_description_id and part.goods_description_id.id or False,
			'carriage_condition_id' : part.carriage_condition_id and part.carriage_condition_id.id or False,
			'modalita_pagamento_id' : part.property_payment_term and part.property_payment_term.id or False,
			'transportation_reason_id' : part.transportation_reason_id and part.transportation_reason_id.id or False,
		}
		if pricelist:
			val['pricelist_id'] = pricelist
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
					location_destinazione = warehouse.location_vendita_banco_id.id
				else:
					location_destinazione = warehouse.lot_stock_id.id
					location_sorgente = warehouse.location_vendita_banco_id.id
				for line in order_obj.vendita_banco_dettaglio_ids:
					if line.product_id:
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
				'state' : 'draft',
				'type' : 'out_invoice',
				'reconciled' : False,
				'fiscal_position' : order_obj.partner_id.property_account_position.id,
				'payment_term' : order_obj.partner_id.property_payment_term.id,
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
		order_obj = self.browse(cr, uid, ids)[0]
		move_obj = self.pool.get('stock.move')
		if (order_obj.state == 'invoiced') and (order_obj.invoice_id):
			message = 'La fattura "%s" e\' collegata a questo ordine\nAccertarsi che essa venga eliminata prima di procedere!' % (order_obj.invoice_id.number or order_obj.invoice_id.name)
			raise osv.except_osv(_('Attenzione!'), _(message))
			return False
		# ----- Cancello i movimenti collegati
		for line in order_obj.vendita_banco_dettaglio_ids:
			if line.move_id:
				move_obj.write(cr, uid, [line.move_id.id], {'state':'draft'})
				move_obj.unlink(cr, uid, [line.move_id.id])
		# ----- Cambio lo stato
		res = {}
		res['state'] = 'draft'
		self.write(cr, uid, order_obj.id, res)
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
			tax_amount = line.tax_id and line.tax_id.amount or 0
			importo = (imponibile * tax_amount) + imponibile
			res[line.id]['importo'] = importo
			res[line.id]['imponibile'] = imponibile
		return res
	

	_columns = {
		'name' : fields.char('Descrizione', size=64),
		'vendita_banco_id' : fields.many2one('vendita_banco', 'vendita_banco', ondelete='cascade'),
		'product_id' : fields.many2one('product.product', 'Prodotto'),
		'product_qty' : fields.float('Quantità'),
		'product_uom' : fields.many2one('product.uom', 'Unità di misura'),
		'price_unit' : fields.float('Prezzo Unitario'),
		'discount' : fields.float('Sconto (%)'),
		'tax_id': fields.many2one('account.tax', 'IVA'),
		'importo' : fields.function(_calcola_importi, method=True, 
			string='Importo', type='float', store=False, multi='sums'),
		'imponibile' : fields.function(_calcola_importi, method=True, 
			string='Imponibile', type='float', store=False, multi='sums'),
		'move_id' : fields.many2one('stock.move', 'Movimento'),
		'invoice_line_id' : fields.many2one('account.invoice.line', 'Linea di fattura'),
	}

	def onchange_product(self, cr, uid, ids, product_id, product_qty, data_ordine, partner_id, pricelist, context={}):
		if product_id:
			res = {}
			product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
			# ----- Aggiunge eventuale IVA presente nel prodotto
			if product_obj.taxes_id:
				res['tax_id'] = product_obj.taxes_id[0].id
			warning = {}
			res['product_uom'] = product_obj.uom_id.id
			res['product_qty'] = 1
			res['name'] = '%s' % (product_obj.name)
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
