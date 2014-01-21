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

from osv import fields,osv
from tools.translate import _


class forza_controllo_congruenza(osv.osv_memory):

    _name = "forza.controllo.congruenza"
    _description = "Forza il controllo congruenza"

    _columns = {
        'name': fields.integer('Arrotondamento Decimali'),
        }
        
    _defaults = {
        'name': 2,
        }

    def forza_controllo(self, cr, uid, ids, context={}):
        causale_ids = self.pool.get('vendita.causali').search(
            cr, uid, [('valuta_congruenza_fattura', '=', True)])
        if not causale_ids:
            raise osv.except_osv(
                _('Attenzione'),
                _('Nessuna causale soggetta a controllo congruenza'))
        wizard = self.browse(cr, uid, ids[0], context)
        vb_obj = self.pool.get('vendita_banco')
        vb_ids = vb_obj.search(
            cr, uid, [('causale', 'in', causale_ids)])
        vendita_ids = [] 
        for vb in vb_obj.browse(cr, uid, vb_ids, context):
            congruente = True
            if vb.invoice_id:
                if round(vb.imponibile, wizard.name) != round(vb.invoice_id.amount_untaxed, wizard.name):
                    congruente = False
                    vendita_ids.append(vb.id)
            vb_obj.write(cr, uid, [vb.id, ], {'conguenza_fattura': congruente})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incongruenza Fattura',
            'res_model': 'vendita_banco',
            'domain' : [('id', 'in', vendita_ids)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'nodestroy': True,
            }

forza_controllo_congruenza()
