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


class stock_warehouse(osv.osv):

	_name = "stock.warehouse"
	_inherit = "stock.warehouse"

	_columns = {
		'location_vendita_banco_id' : fields.many2one('stock.location', 'Location Vendita', required=True,
			help="Indica la location clienti che deve essere utilizzata per i movimenti di magazzino del punto vendita"),
	}

stock_warehouse()


class stock_move(osv.osv):

	_name = "stock.move"
	_inherit = "stock.move"

	_columns = {
		'sorgente_id' : fields.many2one('vendita_banco', 'Sorgente'),
	}

stock_move()
