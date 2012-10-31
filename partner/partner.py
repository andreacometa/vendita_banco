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

class res_partner(osv.osv):

	_name = "res.partner"
	_inherit = "res.partner"

	def _vb_credit(self, cr, uid, ids, name, arg, context=None):
		res = {}
		vb_obj = self.pool.get('vendita_banco')
		for id in ids:
			tot = 0.0
			vb_ids = vb_obj.search(cr, uid, [('state', '=', 'draft'), ('partner_id', '=', id)])
			if vb_ids:
				vbs = vb_obj.browse(cr, uid, vb_ids)
				for vb in vbs:
					tot += vb.totale
			res[id] = tot
		return res

	_columns = {
		'causale' : fields.many2one('vendita.causali', 'Causale', help="Causale predefinita da usare nella vendita al banco"),
		'vb_credit': fields.function(_vb_credit, string='Totale Credito', multi=False, store=False),
	}

res_partner()
