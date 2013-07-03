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

import netsvc
import pooler, tools

from osv import fields, osv
from tools.translate import _

class account_invoice(osv.osv):
	_inherit = 'account.invoice'

	_columns = {
			'packages_number' : fields.integer('Colli'),
			'partner_shipping_id' : fields.many2one('res.partner.address','Indirizzo Spedizione'),
			'tipo_trasporto_id' : fields.many2one('vendita_banco.trasporto', 'Tipo Trasporto'),
		}
account_invoice()


class account_invoice_line(osv.osv):

	_name = "account.invoice.line"
	_inherit = "account.invoice.line"

	_columns = {
		'spesa' : fields.boolean('Spesa', help="Da spuntare se il prodotto è una spesa (trasporto, incasso, etc.)"),
		}
	_defaults = {
		'spesa' : False,
	}

account_invoice_line()
