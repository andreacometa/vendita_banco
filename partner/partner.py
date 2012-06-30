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

	_columns = {
		#'genera_ddt' : fields.boolean('Genera DDT',
		#	help="Indica se il cliente generalmente riceve un DDT al momento della vendita dei prodotti"),
		'causale' : fields.many2one('vendita.causali', 'Causale', help="Causale predefinita da usare nella vendita al banco"),
	}

res_partner()
