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

"""
class stock_warehouse(osv.osv):

	_name = "stock.warehouse"
	_inherit = "stock.warehouse"

	_columns = {
		'location_vendita_banco_id' : fields.many2one('stock.location', 'Location Vendita', required=True,
			help="Indica la location clienti che deve essere utilizzata per i movimenti di magazzino del punto vendita"),
	}

stock_warehouse()
"""

class stock_move(osv.osv):

	_name = "stock.move"
	_inherit = "stock.move"

	_columns = {
		'sorgente_id' : fields.many2one('vendita_banco', 'Sorgente'),
	}

stock_move()
