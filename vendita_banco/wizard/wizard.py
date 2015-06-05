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


class vb_modifica_causale(osv.osv_memory):

    _name = "vb.modifica_causale"
    _description = "Modifica la causale su doc confermati"

    _columns = {
        'nuova_causale' : fields.many2one('vendita.causali', 'Causale', required=True),
        'data' : fields.date('Forza Data', help="Forza l'ordine alla data indicata"),
        # ----- Dati DDT
        'ddt' : fields.boolean('DDT'),
        'goods_description_id' : fields.many2one('stock.picking.goods_description','Aspetto dei beni'),
        'carriage_condition_id' : fields.many2one('stock.picking.carriage_condition','Resa merce'),
        'transportation_reason_id' : fields.many2one('stock.picking.transportation_reason','Causale Trasporto'),
        'number_of_packages' : fields.integer('Numero Colli'),
        'tipo_trasporto_id' : fields.many2one('vendita_banco.trasporto', 'Tipo Trasporto'),
        'trasportatore_id' : fields.many2one('delivery.carrier', 'Trasportatore'),
        'data_inizio_trasporto' : fields.datetime('Data Inizio Trasporto'),
        }

    def onchange_causale(self, cr, uid, ids, causale, context):
        if causale and self.pool.get('vendita.causali').browse(cr,uid,causale).ddt:
            vb = self.pool.get('vendita_banco').browse(cr, uid, context['active_id'])
            return {'value' : {'goods_description_id' : vb.partner_id.goods_description_id and vb.partner_id.goods_description_id.id or False,
                'transportation_reason_id' : vb.partner_id.transportation_reason_id and vb.partner_id.transportation_reason_id.id or False ,
                'carriage_condition_id': vb.partner_id.transportation_reason_id and vb.partner_id.transportation_reason_id.id or False,
                'tipo_trasporto_id': vb.partner_id.tipo_trasporto_id and vb.partner_id.tipo_trasporto_id.id or False,
                'ddt' : True,}}
        else:
            return {'value' : {'goods_description_id' : False,
                'transportation_reason_id' : False ,
                'carriage_condition_id': False,
                'tipo_trasporto_id': False,
                'ddt': False,}}

    def modifica_causale(self, cr, uid, ids, context={}):
        if 'active_id' in context:
            wizard = self.browse(cr, uid, ids[0])
            vb_obj = self.pool.get('vendita_banco')
            vb = vb_obj.browse(cr, uid, context['active_id'])
            if vb.state == 'draft':
                raise osv.except_osv(
                    _('Attenzione!'),
                    _('Questa procedura è applicabile solo agli ordini confermati!'))
            if vb.invoice_id:
                raise osv.except_osv(
                    _('Attenzione!'),
                    _('Impossibile modificare la causale ad un ordine fatturato!'))
            # ----- recuperiamo il protocollo se non è una fattura e se non è spuntata la voce che evita il recupero del protocollo
            if not vb.causale.no_recupera_protocollo_cambio_causale:
                if vb.causale.protocollo != wizard.nuova_causale.protocollo:
                    vb.causale.recupera_protocollo(vb.name, vb.data_ordine)
            # ----- Generiamo un nuovo protocollo
            if vb.causale.protocollo != wizard.nuova_causale.protocollo:
                nuovo_protocollo = wizard.nuova_causale.get_protocollo(
                    wizard.data)
            else:
                nuovo_protocollo = vb.name
            values = {
                'name': nuovo_protocollo,
                'causale': wizard.nuova_causale.id,
                'goods_description_id': False,
                'carriage_condition_id': False,
                'transportation_reason_id': False,
                'number_of_packages': 0,
                'trasportatore_id': False,
                'tipo_trasporto_id': False,
                'ddt': False,
                }
            if wizard.data:
                values.update({'data_ordine':wizard.data})
            if wizard.nuova_causale.ddt:
                values['ddt'] = True
                values['goods_description_id'] = wizard.goods_description_id.id
                values['carriage_condition_id'] = wizard.carriage_condition_id.id
                values['transportation_reason_id'] = wizard.transportation_reason_id.id
                values['number_of_packages'] = wizard.number_of_packages
                values['trasportatore_id'] = wizard.trasportatore_id and wizard.trasportatore_id.id or False
                values['tipo_trasporto_id'] = wizard.tipo_trasporto_id and wizard.tipo_trasporto_id.id or False
                values['data_inizio_trasporto'] = wizard.data_inizio_trasporto or False
            vb_obj.write(cr, uid, [vb.id,], values)
        return {'type': 'ir.actions.act_window_close'}

vb_modifica_causale()
