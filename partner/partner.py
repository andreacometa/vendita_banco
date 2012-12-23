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

class res_partner(osv.osv):

	_name = "res.partner"
	_inherit = "res.partner"

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, uid, ['|',('ref', 'ilike', name), ('name','ilike',name)], limit=limit, context=context)
		return self.name_get(cr, uid, ids, context)

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
		'sconto_fisso' : fields.float('Sconto Fisso', help="Sconto da applicare di dafault al cliente in fase di vendita"),
		'vb_credit': fields.function(_vb_credit, string='Totale Credito', multi=False, store=False),
	}

res_partner()
