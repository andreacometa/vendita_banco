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

class vendita_causali(osv.osv):
	
	_name = "vendita.causali"
	_description = "Vista Causali"
	
	_columns = {
		'name' : fields.char('Codice Causale', size=8, required=True),
		'descrizione' : fields.char('Descrizione', size=32, required=True),
		'tipo' : fields.selection((('carico', 'Carico'), ('scarico', 'Scarico'), ('nessuno', 'Nessuno')),
			'Tipo', select=True, required=True, help="Indicare il tipo causale, identifica il tipo movimentazione in magazzino"),
		'protocollo' : fields.many2one('ir.sequence', 'Protocollo', required=True, help="Indica la nomenclatura da seguire per protocollare il documento"),
		'fatturabile' : fields.boolean('Fatturabile', help="Se spuntato da la possibilità al documento di generare fattura"),
		'ddt' : fields.boolean('Documento di Trasporto', help="Se spuntato da la possibilità al documento di associare dati di trasporto"),
		'report' : fields.many2one('ir.actions.report.xml', 'Report', help="Report di stampa associato"),
		'segno' : fields.selection((('+1', 'Positivo'), ('-1', 'Negativo')), 'Segno', help="Indicare il segno contabile"),
		'fattura' : fields.boolean('Fattura', help="Indica se la causale rappresenta un fattura immediata"),
		'riga_raggruppa' : fields.boolean('Riga Raggruppamento', help="Indica se la generazione della fattura porta le righe descrittive per ogni raggruppamento"),
	}
	
	_defaults = {
		'segno' : '+1',
		'tipo' : 'nessuno',
		'riga_raggruppa': False,
	}
	
	def get_protocollo(self, cr, uid, causale_id):
		if causale_id:
			causale = self.browse(cr, uid, causale_id)[0]
			if not causale.fattura:
				return self.pool.get('ir.sequence').get_id(cr,uid,causale.protocollo.id)
			else:
				return "FAT"
		return False

	def recupera_protocollo(self, cr, uid, ids, protocollo, data_protocollo):
		for c in self.browse(cr,uid,ids):
			self.pool.get('ir.protocolli_da_recuperare').create(cr, uid,
			{'sequence_id':c.protocollo.id, 'protocollo':protocollo, 'data':data_protocollo})
		return True

	# ----- imposta il flag fatturabile 
	def onchange_fattura(self, cr, uid, ids, fattura):
		return  { 'value' : { 'fatturabile' : fattura } }
		
vendita_causali()

