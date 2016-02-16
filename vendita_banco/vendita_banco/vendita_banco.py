# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Andrea Cometa All Rights Reserved.
#                       www.andreacometa.it
#                       openerp@andreacometa.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
import netsvc
from tools.translate import _
import datetime
# import time
import decimal_precision as dp


class vendita_banco_trasporto(osv.osv):
    _name = "vendita_banco.trasporto"
    _description = "Lista Tipologie Trasporto"

    _columns = {
        'name': fields.char('Descrizione', size=64),
        }

vendita_banco_trasporto()


class vendita_banco(osv.osv):
    _name = "vendita_banco"
    _description = "Vendite"

    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'name': False,
            'internal_number': False,
            'invoice_id': False,
            'vb_raggruppamento_id': False,
        })
        return super(vendita_banco, self).copy(cr, uid, id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        vendite = self.browse(cr, uid, ids)
        for vendita in vendite:
            if vendita.state != 'draft':
                raise osv.except_osv(
                    _('Azione non valida!'),
                    _('Impossibile eliminare una vendita validata!'))
            else:
                # if not vendita.causale.fattura and vendita.name:
                if vendita.internal_number:
                    vendita.causale_id.recupera_protocollo(
                        vendita.internal_number, vendita.data_ordine)
                unlink_ids.append(vendita.id)
        return super(vendita_banco, self).unlink(cr, uid, unlink_ids, context)

    def create(self, cr, uid, vals, context=None):
        vals.update({'user_id': uid})
        return super(vendita_banco, self).create(
            cr, uid, vals, context=context)

    # ----- calcola gli importi per ogni riga dell'ordine
    def _calcola_importi(self, cr, uid, ids, field_name, arg, context=None):
        # ----- Calcola il totale della riga di dettaglio
        res = {}
        for vb in self.browse(cr, uid, ids, context):
            res[vb.id] = {'totale': 0.0, 'imponibile': 0.0, }
            for line in vb.vendita_banco_dettaglio_ids:
                res[vb.id]['totale'] += (line.importo * int(vb.causale_id.segno))
                res[vb.id]['imponibile'] += (
                    line.imponibile * int(vb.causale_id.segno))
        return res

    # ----- restituisce true se la causale ha un report in modo da
    # mostrare il button di stampa
    def _get_report(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        vbs = self.browse(cr, uid, ids, context)
        for vb in vbs:
            if vb.causale_id.report:
                res[vb.id] = True
            else:
                res[vb.id] = False
        return res
    """
    def _get_company(self, cr, uid, ids, name, arg, context=None):
        res = {}
        vbs = self.browse(cr, uid, ids, context)
        company_id = self.pool.get('res.company')._company_default_get(
            cr, uid, context=context)
        if not company_id:
            for vb in vbs:
                res[vb.id] = False
        else:
            for vb in vbs:
                res[vb.id] = company_id
        return res
    """
    _columns = {
        'name': fields.char('Numero Documento', size=16),
        'internal_number': fields.char('Internal number', size=16),
        'user_id': fields.many2one('res.users', 'Utente'),
        'data_ordine': fields.date('Data Ordine', required=True),
        'partner_id': fields.many2one('res.partner', 'Cliente', required=True),
        'partner_invoice_id': fields.many2one(
            'res.partner.address',
            'Indirizzo Fatturazione',
            required=True),
        'partner_shipping_id': fields.many2one(
            'res.partner.address',
            'Indirizzo Spedizione'),
        'pricelist_id': fields.many2one(
            'product.pricelist',
            'Listino Prezzi',
            required=True),
        'ddt': fields.related('causale_id', 'ddt', type='boolean',
                              relation='vendita.causali', readonly=True,
                              help="Se la casella è spuntata verrà generato e\
 stampato un DDT altrimenti verrà creato un altro documento"),
        'fatturabile': fields.related('causale_id', 'fatturabile', type='boolean',
                                      relation='vendita.causali',
                                      readonly=True),
        'report': fields.function(_get_report, method=True, type='boolean'),
        'causale_id': fields.many2one('vendita.causali', 'Causale',
                                   required=True),
        'invoice_id': fields.many2one('account.invoice', 'Fattura',
                                      ondelete="set null"),
        'move_id': fields.related(
            'invoice_id', 'move_id', string="Account move",
            type="many2one", relation="account.move", store=False),
        'modalita_pagamento_id': fields.many2one(
            'account.payment.term', 'Modalità di pagamento', required=True),
        # ----- Campi di gestione ddt
        'goods_description_id': fields.many2one(
            'stock.picking.goods_description', 'Aspetto dei beni'),
        'carriage_condition_id': fields.many2one(
            'stock.picking.carriage_condition', 'Resa merce'),
        'transportation_reason_id': fields.many2one(
            'stock.picking.transportation_reason', 'Causale Trasporto'),
        'number_of_packages': fields.integer('Numero Colli'),
        'trasportatore_id': fields.many2one('delivery.carrier',
                                            'Trasportatore'),
        'tipo_trasporto_id': fields.many2one('vendita_banco.trasporto',
                                             'Tipo Trasporto'),
        'data_inizio_trasporto': fields.datetime('Data Inizio Trasporto'),
        # ----- Dettagli
        'vendita_banco_dettaglio_ids': fields.one2many(
            'vendita_banco.dettaglio', 'vendita_banco_id', 'Dettagli',
            ondelete='cascade', readonly=True,
            states={'draft': [('readonly', False)]}),
        'totale': fields.function(
            _calcola_importi, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Totale', type='float', store=True, multi='sums'),
        'imponibile': fields.function(
            _calcola_importi, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Totale Imponibile', type='float', store=True,
            multi='sums'),
        'acconto': fields.float('Acconto',
                                digits_compute=dp.get_precision('Account')),
        'state': fields.selection((
            ('draft', 'Preventivo'), ('done', 'Confermato'),
            ('invoiced', 'Fatturato'), ('validated', 'Validato')),
            'Stato', readonly=True, select=True),
        # ----- Altro
        'note': fields.text('Note'),
        # ----- Wizard
        # --- Contiene l'id di un eventuale doc generato da raggruppamento
        # con wizard
        'vb_raggruppamento_id': fields.many2one(
            'vendita_banco', 'Documento generato', ondelete="set null"),
        'company_id': fields.many2one('res.company', 'Company',
                                      required=False),
        #'company_id': fields.function(_get_company, method=True,
        #                              type='many2one', relation='res.company',
        #                              store=False),
        'picking_id': fields.many2one('stock.picking', 'Picking',
                                      ondelete="set null"),
        # ----- Invoice relations
        'invoice_tax_line_ids': fields.related('invoice_id', 'tax_line',
                                               type='one2many',
                                               relation='account.invoice.tax',
                                               string='Tax Lines'),
        'invoice_payment_ids': fields.related('invoice_id', 'payment_ids',
                                              type='many2many',
                                              relation='account.move.line',
                                              string='Payments'),
        }

    _defaults = {
        'state': 'draft',
        'name': False,
        'internal_number': False,
        'data_ordine': fields.date.context_today,
        'vb_raggruppamento_id': False,
        'company_id': lambda s, cr, uid, c: s.pool[
            'res.company']._company_default_get(cr, uid, 'vendita_banco',
                                                context=c),
    }

    _order = "data_ordine desc, name desc"

    # ----- Funzione che aggiorna il flag ddt
    def onchange_causale(self, cr, uid, ids, causale):
        if causale:
            causale_vals = self.pool.get('vendita.causali').browse(cr,
                                                                   uid,
                                                                   causale)
            warning = {}
            if (not self.pool.get('res.users').browse(cr, uid, uid) in
                    causale_vals.user_ids):
                warning = {
                    'title': 'Attenzione!',
                    'message': 'Non si è abilitati all\'emissione di una \
vendita con questa causale!'
                    }
                causale = False
            ddt = causale_vals.ddt
            return {'value': {
                'ddt': ddt,
                'name': '',
                'causale_id': causale,
                'transportation_reason_id': (
                    causale_vals.transportation_reason_id and
                    causale_vals.transportation_reason_id.id or
                    False)
                }, 'warning': warning}
        return False

    # ----- Funzione che oltre al normale onchange inserisce anche il
    # valore di genera ddt del partner
    def onchange_cliente_id(self, cr, uid, ids, part, causale):
        if not part:
            return {'value': {
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term': False,
                'fiscal_position': False}}
        addr = self.pool.get('res.partner').address_get(
            cr, uid, [part], ['delivery', 'invoice'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        causali_obj = self.pool.get('vendita.causali')
        pricelist = (part.property_product_pricelist and
                     part.property_product_pricelist.id or False)
        causale_id = causale or part.causale_id and part.causale_id.id or False
        causale = causali_obj.browse(cr, uid, causale_id)
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'causale_id': causale_id,
            'ddt': (
                causale_id and
                causale.ddt or False),
            'goods_description_id': (
                part.goods_description_id and
                part.goods_description_id.id or False),
            'carriage_condition_id': (
                part.carriage_condition_id and
                part.carriage_condition_id.id or False),
            'modalita_pagamento_id': (
                part.property_payment_term and
                part.property_payment_term.id or False),
            'transportation_reason_id': ((
                part.transportation_reason_id and
                part.transportation_reason_id.id) or (
                causale_id and causale.transportation_reason_id and
                causale.transportation_reason_id.id) or
                False),
            'tipo_trasporto_id': (
                part.tipo_trasporto_id and
                part.tipo_trasporto_id.id or
                False),
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        return {'value': val}

    # ----- Funzione richiamata dal button Conferma Vendita
    def conferma_vendita(self, cr, uid, ids, *args):
        order_objs = self.browse(cr, uid, ids)
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_id = warehouse_obj.search(cr, uid, [('id', '>', 0)])[0]
        warehouse = warehouse_obj.browse(cr, uid, warehouse_id)
        for order_obj in order_objs:
            picking_id = False
            res = {}
            if order_obj.internal_number:
                res['name'] = order_obj.internal_number
            else:
                res['name'] = order_obj.causale_id.get_protocollo(
                    order_obj.data_ordine)
                res['internal_number'] = res['name']
            if order_obj.causale_id.tipo in ['carico', 'scarico']:
                # se non è un carico/scarico non fa nulla
                if not order_obj.vendita_banco_dettaglio_ids:
                    raise osv.except_osv(
                        _('Azione non valida!'),
                        _('Non esistono righe di vendita per questo ordine!'))
                    # return False
                # ----- CREA UN MOVIMENTO DI MAGAZZINO PER OGNI RIGA DI VENDITA
                location_sorgente = order_obj.causale_id.source_location_id.id
                location_destinazione = order_obj.causale_id.location_id.id
                # create a new picking
                picking_data = {
                    'name': res['name'],
                    'origin': res['name'],
                    'type': (
                        order_obj.causale_id.tipo in ['scarico'] and 'out' or
                        order_obj.causale_id.tipo in ['carico'] and 'in' or
                        'internal'),
                    'location_id': location_sorgente,
                    'location_dest_id': location_destinazione,
                }
                picking_id = self.pool['stock.picking'].create(
                    cr, uid, picking_data, {'lang': 'it_IT'})
                for line in order_obj.vendita_banco_dettaglio_ids:
                    if line.product_id and line.product_id.type != 'service':
                        move_obj = self.pool.get('stock.move')
                        move_valori = {
                            'name': '[%s] %s' % (line.product_id.default_code,
                                                 line.product_id.name),
                            # 'sorgente_id': line.vendita_banco_id.id,
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                            'product_qty': line.product_qty,
                            'product_id': line.product_id.id,
                            'location_id': location_sorgente,
                            'location_dest_id': location_destinazione,
                            'state': 'done',
                            'picking_id': picking_id,
                        }
                        move_id = move_obj.create(cr, uid, move_valori)
                        self.pool.get('vendita_banco.dettaglio').write(
                            cr, uid, line.id, {'move_id': move_id})
            # ----- INSERISCE EVENTUALI LINEE DI SPESA
            if not order_obj.causale_id.no_spesa_incasso:
                for line in order_obj.modalita_pagamento_id.line_ids:
                    if line.spesa_id:
                        vals = {
                            'spesa': True,
                            'name': line.spesa_id.name,
                            'price_unit': line.spesa_id.price,
                            'tax_id': (line.spesa_id.tax_id and
                                       line.spesa_id.tax_id.id),
                            'product_qty': 1,
                            'vendita_banco_id': order_obj.id,
                            'spesa_automatica': True,
                            }
                        self.pool.get('vendita_banco.dettaglio').create(
                            cr, uid, vals)
            # ----- SCRIVE LO STATO
            res['picking_id'] = picking_id or False
            res['state'] = 'done'
            self.write(cr, uid, order_obj.id, res)

            if order_obj.causale_id.fattura:
                invoice_id = self.crea_fatture_raggruppate(
                    cr, uid, ids, order_obj.data_ordine,
                    order_obj.causale_id.name, res['name'],
                    order_obj.internal_number or False)
                # ----- Validate the invoice
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'account.invoice',
                                        invoice_id, 'invoice_open', cr)
                self.write(cr, uid, order_obj.id, {
                    'invoice_id': invoice_id, 'state': 'validated'})
        return True

    def crea_fatture_raggruppate(self, cr, uid, ids, data_fattura, origin,
                                 invoice_number=False, context=None):
        order_objs = self.browse(cr, uid, ids)
        vbanco_dett_obj = self.pool['vendita_banco.dettaglio']
        vbanco_obj = self.pool['vendita_banco']
        invoice_line_obj = self.pool['account.invoice.line']
        journal_id = self.pool['account.invoice']._get_journal(
            cr, uid, {'lang': 'it_IT'})
        account_id = self.pool['account.journal'].browse(
            cr, uid, journal_id).default_credit_account_id.id

        # currency_id = False
        # currency_ids = self.pool.get('res.currency').search(
        #    cr, uid, [('name', '=', 'EUR')])
        # if currency_ids:
        #    currency_id = currency_ids[0]
        # -----
        # CREAZIONE
        # -----
        #import pdb; pdb.set_trace()
        for order_obj in order_objs:
            # -----
            # CREAZIONE TESTATA FATTURA
            # -----
            # account_invoice_id = self.pool.get('account.invoice').create(
            invoice_data = {
                'name': (
                    order_obj.causale_id.fattura and
                    order_obj.causale_id.descrizione or
                    order_obj.name),
                'origin': order_obj.name,
                'date_invoice': data_fattura,
                # 'immediate': order_obj.causale_id.fattura,
                'partner_id': order_obj.partner_id.id,
                'account_id': (
                    order_obj.partner_id.property_account_receivable.id),
                # 'currency_id': currency_id,
                'address_invoice_id': order_obj.partner_invoice_id.id,
                'partner_shipping_id': (
                    order_obj.partner_shipping_id and
                    order_obj.partner_shipping_id.id),
                'state': 'draft',
                'type': 'out_invoice',
                'reconciled': False,
                'fiscal_position': (
                    order_obj.partner_id.property_account_position.id),
                'payment_term': order_obj.modalita_pagamento_id.id,
                'journal_id': (
                    order_obj.causale_id and
                    order_obj.causale_id.journal_id and
                    order_obj.causale_id.journal_id.id or False),
                'comment': order_obj.note,
                'carriage_condition_id': (
                    order_obj.carriage_condition_id and
                    order_obj.carriage_condition_id.id or False),
                'goods_description_id': (
                    order_obj.goods_description_id and
                    order_obj.goods_description_id.id or False),
                'transportation_reason_id': (
                    order_obj.transportation_reason_id and
                    order_obj.transportation_reason_id.id or False),
                'tipo_trasporto_id': (
                    order_obj.tipo_trasporto_id and
                    order_obj.tipo_trasporto_id.id or False),
                'packages_number': order_obj.number_of_packages or 0.0,
                }
            if invoice_number:
                invoice_data['internal_number'] = invoice_number
            account_invoice_id = self.pool['account.invoice'].create(
                cr, uid, invoice_data)
            # CREA UNA RIGA FITTIZIA COME TESTATA
            if order_obj.causale_id.riga_raggruppa:
                invoice_fake_line_id = invoice_line_obj.create(
                    cr, uid, {
                        'name': 'Rif. Ns. %s Nr. %s del %s' % (
                            order_obj.causale_id.descrizione_raggruppamento,
                            order_obj.name,
                            order_obj.data_ordine),
                        'invoice_id': account_invoice_id,
                        'quantity': 0,
                        'account_id': account_id,
                        'price_unit': 0.0,
                    })
            # ----- CREA LE RIGHE REALI DEI PRODOTTI
            for line in order_obj.vendita_banco_dettaglio_ids:
                invoice_line_tax_id = (
                    line.tax_id and [(6, 0, [line.tax_id.id])] or False)
                # Il codice seguente deve essere implementato nei clienti che
                # hanno il calcolo dello sconto dinamico
                # price_unit = (100 * line.imponibile) / (100 - line.discount)
                # price_unit = price_unit / line.product_qty
                invoice_line_id = invoice_line_obj.create(cr, uid, {
                    'name': line.name,
                    'invoice_id': account_invoice_id,
                    'product_id': (
                        line.product_id and line.product_id.id or False),
                    'quantity': line.product_qty,
                    'account_id': (
                        line.product_id and
                        line.product_id.product_tmpl_id.property_account_income.id or
                        account_id),
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'partner_id': line.vendita_banco_id.partner_id.id,
                    'invoice_line_tax_id': invoice_line_tax_id,
                    'uos_id': line.product_uom.id,
                    'spesa': line.spesa,
                    'spesa_automatica': line.spesa_automatica,
                    })
                vbanco_dett_obj.write(
                    cr, uid, [line.id], {'invoice_line_id': invoice_line_id})
            # modifica lo stato
            vbanco_obj.write(cr, uid, [order_obj.id], {
                'invoice_id': account_invoice_id, 'state': 'invoiced'})
        # ----- Salva in vendita_banco la fattura appena creata e
        # modifica lo stato
        # self.write(cr, uid, ids, {
        #    'invoice_id': account_invoice_id, 'state': 'invoiced'})
        # ----- MOSTRA LA FATTURA APPENA CREATA
        # mod_obj = self.pool.get('ir.model.data')
        # res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        # res_id = res and res[1] or False,
        # return {
        #    'name': 'Customer Invoices',
        #    'view_type': 'form',
        #    'view_mode': 'form',
        #    'view_id': [res_id],
        #    'res_model': 'account.invoice',
        #    'context': "{'type':'out_invoice'}",
        #    'type': 'ir.actions.act_window',
        #    'nodestroy': True,
        #    'target': 'current',
        #    'res_id': account_invoice_id or False,
        # }
        return account_invoice_id

    # ----- Funzione che crea la fattura dal button nel form
    def crea_fattura(self, cr, uid, ids, context={}):
        data_fattura = datetime.datetime.today()
        data_fattura = '%s/%s/%s' % (
            data_fattura.strftime('%d'),
            data_fattura.strftime('%m'),
            data_fattura.strftime('%Y'))
        order = self.browse(cr, uid, ids[0])
        return self.crea_fatture_raggruppate(
            cr, uid, ids, data_fattura, order.name,
            order.causale_id.fattura and order.internal_number or False,
            context)

    def create_so_invoice(self, cr, uid, ids, context={}):
        orders = self.browse(cr, uid, ids)
        so_obj = self.pool['vendita_banco']
        so_lines_obj = self.pool['vendita_banco.dettaglio']
        # ----- Controlla che tutti i documenti siano confermati
        for order in orders:
            if order.state == 'draft':
                raise osv.except_osv(
                    _('Attention!'),
                    _('All orders must be confirmed to proceed!'))
            if order.causale_id.invoice_template_id is False:
                raise osv.except_osv(
                    _('Attention!'),
                    _('Orders with template %s has no invoicing template!' % (
                        wizard.new_template_id.name)))
            # ----- Genera la testa del nuovo documento
            so_data = {
                'partner_id': order.partner_id.id,
                'partner_invoice_id': order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'pricelist_id': order.pricelist_id.id,
                'modalita_pagamento_id': order.modalita_pagamento_id.id,
                'causale_id': order.causale_id.invoice_template_id.id,
                'goods_description_id': order.goods_description_id.id,
                'carriage_condition_id': order.carriage_condition_id.id,
                'transportation_reason_id': order.transportation_reason_id.id,
                'number_of_packages': order.number_of_packages,
                'trasportatore_id': order.trasportatore_id.id,
            }
            new_order_id = so_obj.create(cr, uid, so_data)
            # ----- Indica il nuovo ordine in quelli vecchi
            so_obj.write(cr, uid, order.id,
                         {'order_group_id': new_order_id})
            # ----- Genera i dettagli del nuovo documento
            # ----- Crea la riga descrittiva di riferimento
            so_line_data = {
                'name': 'Rif. Ns. %s Nr. %s del %s' % (
                    order.causale_id.descrizione_raggruppamento, order.name,
                    order.data_ordine),
                'vendita_banco_id': new_order_id,
                'product_id': False,
                'product_uom': False,
                'product_qty': 0.0,
                'price_unit': 0.0,
                'tax_id': False,
            }
            so_lines_obj.create(cr, uid, so_line_data)
            for line in order.vendita_banco_dettaglio_ids:
                # ----- Crea la righe dei prodotti
                so_line_data = {
                    'name': line.name,
                    'vendita_banco_id': new_order_id,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'tax_id': line.tax_id and line.tax_id.id,
                    'discount': line.discount,
                    'spesa': line.spesa,
                    'spesa_automatica': line.spesa_automatica,
                }
                so_lines_obj.create(cr, uid, so_line_data)
            # ----- Mostra il documento appena creato
            mod_obj = self.pool['ir.model.data']
            res = mod_obj.get_object_reference(cr, uid, 'vendita_banco',
                                               'view_vendita_banco_form')
            res_id = res and res[1] or False,
            return {
                'name': 'Vendita banco',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': res_id,
                'res_model': 'vendita_banco',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': new_order_id or False,
            }
        return False

    # ----- Funzione richiamata dal button Conferma Vendita
    def riapri_vendita(self, cr, uid, ids, *args):
        for order_obj in self.browse(cr, uid, ids):
            move_obj = self.pool['stock.move']
            picking_obj = self.pool['stock.picking']
            # ----- Controlla che non ci siano fatture generate da questi ord
            if ((order_obj.state in ['invoiced', 'validated']) and
                    (order_obj.invoice_id)):
                # check for payments
                if order_obj.invoice_id.payment_ids:
                    message = 'Invoice has payments, you should delete them!'
                    raise osv.except_osv(_('Attention!'), _(message))
                # reopen invoice
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'account.invoice',
                                        order_obj.invoice_id.id,
                                        'invoice_cancel', cr)
                invoice_obj = self.pool['account.invoice']
                self.pool['ir.protocolli_da_recuperare'].create(
                    cr, uid, {
                        'name': ' account.journal',
                        'protocollo': order_obj.invoice_id.internal_number,
                        'data': order_obj.invoice_id.date_invoice,
                        'sequence_id': order_obj.invoice_id.journal_id.sequence_id.id, })
                invoice_obj.write(cr, uid, [order_obj.invoice_id.id],
                                  {'internal_number': False})
                invoice_obj.unlink(cr, uid, [order_obj.invoice_id.id])

            # ----- Controlla che non ci siano ordini di raggruppamento
            # generati da questi ordini
            if order_obj.vb_raggruppamento_id:
                message = 'L\'ordine di raggruppamento "%s" e\' collegata a\
 questo ordine\nAccertarsi che essa venga eliminata prima di procedere!' % (
                    order_obj.vb_raggruppamento_id.name)
                raise osv.except_osv(_('Attenzione!'), _(message))
                return False
            # ----- Cancello i movimenti collegati
            if order_obj.picking_id:
                move_ids = move_obj.search(
                    cr, uid, [('origin', '=', order_obj.name)])
                move_obj.write(cr, uid, move_ids, {'state': 'draft'})
                picking_obj.write(
                    cr, uid, [order_obj.picking_id.id], {'state': 'draft'}, )
                picking_obj.unlink(cr, uid, [order_obj.picking_id.id])
            for line in order_obj.vendita_banco_dettaglio_ids:
                #if line.move_id and move_obj.browse(cr,uid,line.move_id.id):
                # move_obj.write(cr, uid, [line.move_id.id], {'state':'draft'})
                # move_obj.unlink(cr, uid, [line.move_id.id])
                if line.spesa_automatica:
                    self.pool.get('vendita_banco.dettaglio').unlink(
                        cr, uid, [line.id, ])
        # ----- Cambio lo stato
        res = {}
        res['state'] = 'draft'
        self.write(cr, uid, ids, res)
        return True

    # ----- Funzione richiamata dal button Stampa BC o DDT
    def stampa(self, cr, uid, ids, context=None):
        order_obj = self.browse(cr, uid, ids[0])
        if order_obj.causale_id.fattura:
            return order_obj.invoice_id.print_imm_diff_invoice(
                [order_obj.invoice_id.id])
            #return {
            #    # ----- Jasper Report
            #    'type': 'ir.actions.report.xml',
            #    'report_name': report_name,
            #    'datas': {
            #        'model': 'account_invoice',
            #        'ids': ids,
            #        'report_type': 'pdf',
            #    },
            #    'nodestroy': True,
            #}
        else:
            report_name = order_obj.causale_id.report.report_name
            return {
                # ----- Jasper Report
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': {
                    'model': 'vendita_banco',
                    'ids': ids,
                    'report_type': 'pdf',
                },
                'nodestroy': True,
            }
vendita_banco()


class vendita_banco_dettaglio(osv.osv):

    _name = "vendita_banco.dettaglio"
    _description = "Vendite"

    # ----- calcola gli importi per ogni riga dell'ordine
    def _calcola_importi(self, cr, uid, ids, field_name, arg, context=None):
        # ----- Calcola il totale della riga di dettaglio
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = {'importo': 0.0, 'imponibile': 0.0, }
            imponibile = line.price_unit * line.product_qty
            # ----- applica lo sconto
            if line.discount:
                #sconto = imponibile * line.discount
                #imponibile = imponibile - sconto
                imponibile = imponibile * (1 - (line.discount / 100.00))
            tax_amount = line.tax_id and line.tax_id.amount or 0
            importo = (imponibile * tax_amount) + imponibile
            res[line.id]['importo'] = importo
            res[line.id]['imponibile'] = imponibile
        return res

    _columns = {
        'name': fields.char('Descrizione', size=64),
        'vendita_banco_id': fields.many2one('vendita_banco', 'Vendita',
                                            ondelete='cascade'),
        'partner_id': fields.related(
            'vendita_banco_id', 'partner_id', string="Cliente",
            type="many2one", relation="res.partner", store=True),
        'causale_id': fields.related(
            'vendita_banco_id', 'causale_id', string="Causale", type="many2one",
            relation="vendita.causali", store=True),
        'data_ordine': fields.related(
            'vendita_banco_id', 'data_ordine', string="Data Vendita",
            type="date", store=True),
        'product_id': fields.many2one('product.product', 'Prodotto'),
        'product_qty': fields.float('Quantità'),
        'product_uom': fields.many2one('product.uom', 'Unità di misura'),
        'price_unit': fields.float(
            'Prezzo Unitario',
            digits_compute=dp.get_precision('Vendita Banco Dettaglio')),
        'discount': fields.float(
            'Sconto (%)', help="Indicare uno sconto in percentuale"),
        'tax_id': fields.many2one('account.tax', 'IVA'),
        'importo': fields.function(
            _calcola_importi, method=True,
            digits_compute=dp.get_precision('Vendita Banco Dettaglio'),
            string='Importo', type='float', store=False, multi='sums'),
        'imponibile': fields.function(
            _calcola_importi, method=True,
            digits_compute=dp.get_precision('Vendita Banco Dettaglio'),
            string='Imponibile', type='float', store=False, multi='sums'),
        'move_id': fields.many2one('stock.move', 'Movimento'),
        'invoice_line_id': fields.many2one(
            'account.invoice.line', 'Linea di fattura'),
        'spesa': fields.boolean('Spesa'),  # gestione spese di incasso
        'spesa_automatica': fields.boolean('Spesa Automatica'),
        # individua le righe di spesa inserite automaticamente
        'note': fields.text('Note'),
        'sequence': fields.integer('Ordine'),
    }
    _defaults = {
        'spesa': False,
        'spesa_automatica': False,
        'sequence': -1,
    }
    _order = "sequence asc"

    def create(self, cr, uid, vals, context=None):
        if vals['product_qty'] > 0 and not vals['tax_id']:
            raise osv.except_osv(
                _('Attenzione!'),
                _('Riga senza IVA nel documento \n>> {0}'.format(vals['name'])))
        if ('sequence' not in vals):  # and vals['sequence'] < 1):
            vbd_obj = self.pool.get('vendita_banco.dettaglio')
            vbd_ids = vbd_obj.search(
                cr, uid, [
                    ('vendita_banco_id', '=', vals['vendita_banco_id'])],
                order='sequence desc')
            if vbd_ids:
                vals.update(
                    {'sequence':
                     vbd_obj.browse(cr, uid, vbd_ids[0]).sequence + 1})
            else:
                vals.update({'sequence': 1})
        return super(vendita_banco_dettaglio, self).create(
            cr, uid, vals, context=context)

    '''
    def write(self, cr, uid, ids, vals, context=None):
        print "write \t%s" % vals
        #vals.update({'user_id':uid})
        return super(vendita_banco_dettaglio,self).write(
            cr, uid, ids, vals, context=context)
    '''
    def onchange_product(self, cr, uid, ids, product_id, product_qty,
                         data_ordine, partner_id, pricelist, tax_id=False,
                         context={}):
        if product_id:
            res = {}
            product_obj = self.pool.get('product.product').browse(
                cr, uid, product_id)
            # ----- Aggiunge eventuale IVA presente nel prodotto
            if (not tax_id) and (product_obj.taxes_id):
                res['tax_id'] = product_obj.taxes_id[0].id
            warning = {}
            res['product_uom'] = product_obj.uom_id.id
            res['product_qty'] = 1
            if product_obj.default_code:
                res['name'] = '[%s] %s' % (
                    product_obj.default_code, product_obj.name)
            else:
                res['name'] = '%s' % (product_obj.name)
            res['spesa'] = product_obj.spesa
            # ----- richiama lo sconto fisso
            if partner_id:
                res['discount'] = self.pool.get('res.partner').browse(
                    cr, uid, partner_id).sconto_fisso
            if not pricelist:
                warning = {
                    'title': 'Nessun Listino!',
                    'message': 'Selezionare un listino di vendita o associarne\
 uno al cliente!'
                    }
            else:
                price = self.pool.get('product.pricelist').price_get(
                    cr, uid, [pricelist], product_id, product_qty or 1.0,
                    partner_id, {
                        'uom': product_obj.uom_id.id,
                        'date': data_ordine,
                    })[pricelist]
                if price is False:
                    warning = {
                        'title': 'Nessuna linea del listino valida trovata!',
                        'message': 'Impossibile trovare una linea del listino \
valida per questo prodotto.'
                        }
                else:
                    res['price_unit'] = price
            return {'value': res, 'warning': warning}
        return False

vendita_banco_dettaglio()
