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
from tools.translate import _
from datetime import datetime
import time


# -------------------------------------------------------
#		CREA FATTURE RAGGRUPPATE
# -------------------------------------------------------
class vb_raggruppa_fatture(osv.osv_memory):

    _name = "vb.raggruppa_fatture"
    _description = "Crea più fatture raggruppate in una volta sola"

    _columns = {
        'filtro_data_inizio': fields.date('Data Inizio', required=True),
        'filtro_data_fine': fields.date('Data Fine', required=True),
        'ordini_ids': fields.one2many('vb.ordini_da_fatturare',
                                      'vb_raggruppa_fatture_id',
                                      'Documenti da fatturare'),
        'raggruppa': fields.boolean(
            'Raggruppa',
            help="Raggruppa gli ordini dello stesso cliente e crea un'unica \
fattura."),
        'data_fattura': fields.date('Data fattura', required=True),
        'filtrato': fields.boolean('Filtrato'),
        'cliente': fields.many2one('res.partner', "Cliente"),
        'modalita_pagamento_id': fields.many2one('account.payment.term',
                                                 'Modalità di pagamento'),
        'causale_id': fields.many2one('vendita.causali', 'Causale'),
        'raggruppa_per_termine_pagamento': fields.boolean(
            'Raggruppa per termini pagamento',
            help="Raggruppa i documenti in base ai termini di pagamento, \n\
lasciare libero se si vuole generare un'unica fattura indipendente dai \
termini di pagamento")
    }
    _defaults = {
        'data_fattura': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def filtra_ordini(self, cr, uid, ids, context={}):
        wizard_obj = self.browse(cr, uid, ids)[0]

        # cerchiamo anche le causali FATTURABILI oltre ai documenti
        # NON ancora fatturati
        search_arg = [
            ('data_ordine', '<=', wizard_obj.filtro_data_fine),
            ('data_ordine', '>=', wizard_obj.filtro_data_inizio),
            ('invoice_id', '=', None), ('state', '!=', 'draft'),
            ('fatturabile', '=', True), ('vb_raggruppamento_id', '=', None)]

        # se presente il cliente
        if wizard_obj.cliente:
            search_arg.append(('partner_id', '=', wizard_obj.cliente.id))

        # se presente payment term
        if wizard_obj.modalita_pagamento_id:
            search_arg.append(
                ('modalita_pagamento_id', '=',
                 wizard_obj.modalita_pagamento_id.id))

        # se presente la causale
        if wizard_obj.causale_id:
            search_arg.append(('causale', '=', wizard_obj.causale_id.id))

        vendita_banco_ids = self.pool.get('vendita_banco').search(
            cr, uid, search_arg, order='partner_id,modalita_pagamento_id')
        if vendita_banco_ids:
            ordini_da_fatturare_obj = self.pool.get('vb.ordini_da_fatturare')
            for vendita_banco_id in vendita_banco_ids:
                ordini_da_fatturare_obj.create(cr, uid, {
                    'name': vendita_banco_id,
                    'vb_raggruppa_fatture_id': wizard_obj.id})
        else:
            raise osv.except_osv(
                _('Attenzione!'),
                _('Impossibile trovare documenti da fatturare per il cliente \
selezionato!'))
            return {'type': 'ir.actions.act_window_close'}
        self.write(cr, uid, ids, {'filtrato': True})
        return True

    def genera_fatture_raggruppate(self, cr, uid, ids, doc_objs, context={}):
        '''
        @ids lista id documenti ordinati per cliente, modalità pagamento
        '''
        partner_obj = self.pool.get('res.partner')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        vbanco_obj = self.pool.get('vendita_banco')
        wizard_obj = self.browse(cr, uid, ids)[0]
        journal_ids = self.pool.get('account.journal').search(
            cr, uid, [('type', '=', 'sale')])
        journal_id = journal_ids[0]
        account_id = self.pool.get('account.account').search(
            cr, uid, [('code', '=', '310100')])[0]
        # qui andrebbe richiamata la partita dal prodotto
        currency_id = False
        currency_ids = self.pool.get('res.currency').search(
            cr, uid, [('name', '=', 'EUR')])
        if currency_ids:
            currency_id = currency_ids[0]

        data_fattura = wizard_obj.data_fattura

        cliente = False
        modalita = False
        account_invoice_ids = []
        nriga = 0

        for doc in doc_objs:
            order_obj = doc.name
            # -----
            # CREAZIONE TESTATA FATTURA
            # -----
            # controlliamo se cambiare
            if (cliente != order_obj.partner_id.id or
                (modalita != order_obj.modalita_pagamento_id.id and
                 wizard_obj.raggruppa_per_termine_pagamento)):
                # nuova fattura
                addr = partner_obj.address_get(cr, uid,
                                               [order_obj.partner_id.id],
                                               ['delivery', 'invoice'])
                account_invoice_id = invoice_obj.create(cr, uid, {
                    'name': "Fattura Differita (%s)" % order_obj.name,
                    'date_invoice': data_fattura,
                    'partner_id': order_obj.partner_id.id,
                    'account_id': order_obj.partner_id.property_account_receivable.id,
                    'journal_id': (order_obj.causale and
                                   order_obj.causale.journal_id and
                                   order_obj.causale.journal_id.id or
                                   journal_id),
                    'currency_id': currency_id,
                    'address_invoice_id': addr['invoice'],
                    'state': 'draft',
                    'type': 'out_invoice',
                    'reconciled': False,
                    'fiscal_position': order_obj.partner_id.property_account_position.id,
                    'payment_term': order_obj.modalita_pagamento_id.id,
                })
                cliente = order_obj.partner_id.id
                modalita = order_obj.modalita_pagamento_id.id
                nriga = 0
            # dettaglio
            if order_obj.causale.riga_raggruppa:
                nriga += 1
                invoice_fake_line_id = invoice_line_obj.create(cr, uid, {
                    'name': 'Rif. Ns. %s Nr. %s del %s' % (
                        order_obj.causale.descrizione_raggruppamento,
                        order_obj.name, order_obj.data_ordine),
                    'invoice_id': account_invoice_id,
                    'quantity': 1,
                    'account_id': account_id,
                    'price_unit': 0.0,
                    'sequence': nriga,
                })
            # ----- CREA LE RIGHE REALI DEI PRODOTTI
            for line in order_obj.vendita_banco_dettaglio_ids:
                nriga += 1
                invoice_line_tax_id = (line.tax_id and
                                       [(6, 0, [line.tax_id.id])] or False)
                struttura_dati = {
                    'name': line.name,
                    'invoice_id': account_invoice_id,
                    'product_id': (line.product_id and line.product_id.id or
                                   False),
                    'quantity': line.product_qty,
                    'account_id': account_id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'partner_id': line.vendita_banco_id.partner_id.id,
                    'invoice_line_tax_id': invoice_line_tax_id,
                    'sequence': nriga,
                    'uos_id': line.product_uom and line.product_uom.id,
                    'spesa': line.spesa,
                    }
                invoice_line_id = invoice_line_obj.create(
                    cr, uid, struttura_dati)
                self.pool.get('vendita_banco.dettaglio').write(
                    cr, uid, [line.id], {'invoice_line_id': invoice_line_id})
            # ----- Salva in vendita_banco la fattura appena creata
            # e modifica lo stato
            vbanco_obj.write(cr, uid, [order_obj.id], {
                'invoice_id': account_invoice_id, 'state': 'invoiced'})
            account_invoice_ids.append(account_invoice_id)

        # ----- MOSTRA LA FATTURA APPENA CREATA
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False,
        return {
            'name': 'Customer Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': account_invoice_ids or False,
        }

    def crea_fatture(self, cr, uid, ids, context={}):
        wizard_obj = self.browse(cr, uid, ids)[0]
        # ----- Crea una fattura per ogni linea selezionata
        if wizard_obj.raggruppa:
            #effettua il raggruppamento delle fatture
            self.genera_fatture_raggruppate(
                cr, uid, ids, wizard_obj.ordini_ids)
        else:
            for ordine in wizard_obj.ordini_ids:
                origin = ordine.name.name
                ordine.name.crea_fatture_raggruppate(
                    wizard_obj.data_fattura, origin, {})

        return {'type': 'ir.actions.act_window_close'}

vb_raggruppa_fatture()


# -------------------------------------------------------
#		ORDINI DA FATTURARE
# -------------------------------------------------------
class vb_ordini_da_fatturare(osv.osv_memory):

    _name = "vb.ordini_da_fatturare"
    _description = "Lista ordini da fatturare"

    _columns = {
        'name': fields.many2one('vendita_banco', 'Ordine'),
        'partner_id': fields.related('name', 'partner_id', type="many2one",
                                     relation="res.partner", string='Cliente'),
        'totale': fields.related('name', 'totale', type="float",
                                 string='Totale'),
        'imponibile': fields.related('name', 'imponibile', type="float",
                                     string='Imponibile'),
        'vb_raggruppa_fatture_id': fields.many2one('vb.raggruppa_fatture',
                                                   'Raggruppa'),
        'modalita_pagamento_id': fields.related(
            'name', 'modalita_pagamento_id', type="many2one",
            relation="account.payment.term", string='Modalità di pagamento'),
        'data_documento': fields.related('name', 'data_ordine', type='date',
                                         string='Data Documento'),
        }

vb_ordini_da_fatturare()
