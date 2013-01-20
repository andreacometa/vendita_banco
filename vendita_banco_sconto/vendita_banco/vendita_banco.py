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
import decimal_precision as dp

class vendita_banco(osv.osv):

	_name = "vendita_banco"
	_inherit = "vendita_banco"

	# aggiunge lo sconto sugli importi totali del documento
	def _calcola_importi(self, cr, uid, ids, field_name, arg, context=None):
		res = super(vendita_banco, self)._calcola_importi(cr,uid,ids,field_name,arg,context)
		vbs = self.browse(cr, uid, ids, context)
		for vb in vbs:
			if vb.sconto_globale > 0.0:
				sconto = (100 - vb.sconto_globale) / 100
				res[vb.id]['totale'] *= sconto
				res[vb.id]['imponibile'] *= sconto
		return res
				
	_columns = {
		'totale' : fields.function(_calcola_importi, method=True, 
			digits_compute=dp.get_precision('Account'),
			string='Totale', type='float', store=True, multi='sums'),
		'imponibile' : fields.function(_calcola_importi, method=True,
			digits_compute=dp.get_precision('Account'),
			string='Totale Imponibile', type='float', store=True, multi='sums'),
		'sconto_globale' : fields.float("Sconto Globale", help="inserire uno sconto globale per il documento, in percentuale [0-100]"),
	}
	_defaults = {
		'sconto_globale' : 0.0,
	}
	
vendita_banco()
