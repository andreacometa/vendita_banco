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


class vendita_causali(osv.osv):
    _name = "vendita.causali"
    _description = "Vista Causali"

    _columns = {
        'name': fields.char('Codice Causale', size=8, required=True),
        'descrizione': fields.char('Descrizione', size=32, required=True),
        'tipo': fields.selection(
            (('carico', 'Carico'), ('scarico', 'Scarico'),
             ('nessuno', 'Nessuno')),
            'Tipo', select=True, required=True,
            help="Indicare il tipo causale, identifica il tipo movimentazione \
in magazzino"),
        'protocollo': fields.many2one(
            'ir.sequence', 'Protocollo', required=True,
            help="Indica la nomenclatura da seguire per protocollare il \
documento"),
        'fatturabile': fields.boolean(
            'Fatturabile',
            help="Se spuntato da la possibilità al documento di generare \
fattura"),
        'invoice_template_id': fields.many2one(
            'vendita.causali', 'Causale fattura',
            help="Select the template for invoicing this document"),
        'ddt': fields.boolean(
            'Documento di Trasporto',
            help="Se spuntato da la possibilità al documento di associare dati\
 di trasporto"),
        'report': fields.many2one(
            'ir.actions.report.xml', 'Report',
            help="Report di stampa associato"),
        'segno': fields.selection(
            (('+1', 'Positivo'), ('-1', 'Negativo')), 'Segno',
            help="Indicare il segno contabile"),
        'fattura': fields.boolean(
            'Fattura',
            help="Indica se la causale rappresenta un fattura immediata"),
        'journal_id': fields.many2one(
            'account.journal', 'Sezionale',
            help="Imposta un sezionale che verrà automaticamente inserito nell\
a fattura generata"),
        'riga_raggruppa': fields.boolean(
            'Riga Raggruppamento',
            help="Indica se la generazione della fattura porta le righe \
descrittive per ogni raggruppamento"),
        'location_id': fields.many2one(
            'stock.location', 'Dest Location',
            help="Indica se, usando questa causale, si deve muovere la merce \
verso una location differente rispetto a quella standard"),
        'source_location_id': fields.many2one(
            'stock.location', 'Source Location',
            help="Indica se, usando questa causale, si deve muovere la merce \
da una location differente rispetto a quella standard"),
        'user_ids': fields.many2many('res.users',
                                     'res_users_causali_rel',
                                     'user_id',
                                     'causale_id',
                                     'Utenti Abilitati'),
        'raggruppamento_ids': fields.many2many('vendita.causali',
                                               'causali_raggruppamento_rel',
                                               'causale_raggruppamento_id',
                                               'causale_id',
                                               'Causali Raggruppamento'),
        'no_recupera_protocollo_cambio_causale': fields.boolean(
            'Non Recuperare Protocollo al Cambio Causale',
            help='Se spuntata, indica che, al cambio di causale, il protocollo\
 deve essere perso'),
        'descrizione_raggruppamento': fields.char(
            'Descrizione Raggruppamento',
            size=16, required=True,
            help="Indica la stringa da riportare in raggruppamento nella fattura"),
        'no_spesa_incasso': fields.boolean(
            'No Spesa Incasso',
            help='Indica che la causale non è soggetta a spesa d\'incasso'),
        'transportation_reason_id': fields.many2one(
            'stock.picking.transportation_reason',
            'Causale Trasporto predefinita'),

    }

    _defaults = {
        'segno': '+1',
        'tipo': 'nessuno',
        'riga_raggruppa': False,
        'descrizione_raggruppamento': "Documento",
        'invoice_template_id': False,
    }

    def get_protocollo(self, cr, uid, causale_id, date):
        if causale_id:
            causale = self.browse(cr, uid, causale_id)[0]
            fiscalyear_id = self.pool['account.fiscalyear'].search(
                cr, uid, [('date_start', '<=', date),
                          ('date_stop', '>=', date)]
            )
            c = {'fiscalyear_id': fiscalyear_id and fiscalyear_id[0] or False}
            return self.pool.get('ir.sequence').next_by_id(
                cr, uid, causale.protocollo.id, c)
        else:
            raise osv.except_osv(
                _("Attention!"),
                _("No sequence defined for this template"))
            # return False

    def recupera_protocollo(self, cr, uid, ids, protocollo, data_protocollo):
        for c in self.browse(cr, uid, ids):
            exists = self.pool['ir.protocolli_da_recuperare'].search(cr, uid, [
                ('name', '=', c.fattura and 'account.journal' or c.descrizione),
                ('protocollo', '=', protocollo),
                ('data', '=', data_protocollo)])
            if exists:
                continue
            self.pool['ir.protocolli_da_recuperare'].create(
                cr, uid, {
                    'name': c.fattura and 'account.journal' or c.descrizione,
                    'sequence_id': c.protocollo.id,
                    'protocollo': protocollo,
                    'data': data_protocollo,
                })
        return True

    #  ----- imposta il flag fatturabile
    def onchange_fattura(self, cr, uid, ids, fattura):
        res = {'value': {}}
        if not fattura:
            res['value']['journal_id'] = False
        res['value']['fatturabile'] = fattura
        return res

vendita_causali()
