# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Andrea Cometa All Rights Reserved.
#                       www.andreacometa.it
#                       openerp@andreacometa.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License
#    as published by
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
        'packages_number': fields.integer('Colli'),
        'partner_shipping_id': fields.many2one(
            'res.partner.address', 'Indirizzo Spedizione'),
        'tipo_trasporto_id': fields.many2one(
            'vendita_banco.trasporto', 'Tipo Trasporto'),
        }

    def action_date_assign(self, cr, uid, ids, *args):
        default_account_id = self.pool.get('account.account').search(
            cr, uid, [('code', '=', '310100')])[0]
        for inv in self.browse(cr, uid, ids):
            if inv.type not in ('in_invoice', 'in_refund'):
                if not inv.payment_term:
                    raise osv.except_osv(
                        _('Attenzione!'),
                        _('È necessario un termine di pagamento'))
                # ----- Aggiunge automaticamente le righe di spesa/e
                for line in inv.payment_term.line_ids:
                    if not line.spesa_id:
                        continue
                    if line.spesa_id.account_id:
                        account_id = line.spesa_id.account_id.id
                    else:
                        account_id = default_account_id
                    vals = {
                        'spesa': True,
                        'name': line.spesa_id.name,
                        'price_unit': line.spesa_id.price,
                        'tax_id': line.spesa_id.tax_id and [(6, 0, [line.spesa_id.tax_id.id])] or False,
                        'quantity': 1,
                        'invoice_id': inv.id,
                        'account_id': account_id,
                        'spesa_automatica': True,
                        }
                    self.pool.get('account.invoice.line').create(cr, uid, vals)
        return super(account_invoice, self).action_date_assign(cr, uid,
                                                               ids, args)

    def action_cancel_draft(self, cr, uid, ids, *args):
        res = super(account_invoice, self).action_cancel_draft(
            cr, uid, ids, args)
        line_obj = self.pool['account.invoice.line']
        for inv in self.browse(cr, uid, ids):
            # ----- Elimina le righe di spesa/e create automaticamente
            for line in inv.invoice_line:
                if line.spesa_automatica:
                    line_obj.unlink(cr, uid, [line.id])
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).unlink(cr, uid, ids, context)
        # riporta lo stato a 'done'
        if res:
            vb_model = self.pool['vendita_banco']
            vb_ids = vb_model.search(
                cr, uid, [('invoice_id', 'in', ids)])
            vb_model.write(cr, uid, vb_ids, {'state': 'done'})
        return res

account_invoice()


class account_invoice_line(osv.osv):

    _name = "account.invoice.line"
    _inherit = "account.invoice.line"

    _columns = {
        'spesa': fields.boolean(
            'Spesa',
            help="Da spuntare se il prodotto è una spesa (trasporto, incasso, etc.)"),
        'spesa_automatica': fields.boolean('Spesa Automatica'),
        }

    _defaults = {
        'spesa': False,
        'spesa_automatica': False,
    }

account_invoice_line()
