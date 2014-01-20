# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012 Francesco OpenCode Apruzzese (<cescoap@gmail.com>)
#    All Rights Reserved
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


class vendita_causali(osv.osv):

    _name = "vendita.causali"
    _inherit = "vendita.causali"

    _columns = {
        'valuta_congruenza_fattura': fields.boolean(
            'Valuta Congruenza fattura',
            help='Spuntare se si vuole analizzare la congruenza tra il \
                  documento con questa causale e la fattura generata'),
        }

vendita_causali()


class vendita_banco(osv.osv):

    _name = "vendita_banco"
    _inherit = "vendita_banco"

    def _conguenza_fattura(self, cr, uid, ids, name, arg, context=None):
        res = {}
        # ----- Diamo per scontato che il documento sia conguente
        #       in modo da non avere falsi positivi con documenti
        #       che non hanno la causale fattura
        for vb in self.browse(cr, uid, ids):
            congruente = True
            if vb.causale.valuta_congruenza_fattura and vb.invoice_id:
                if vb.imponibile != vb.invoice_id.amount_untaxed:
                    congruente = False
            res.update({vb.id: congruente})
        return res

    _columns = {
        'conguenza_fattura': fields.function(
            _conguenza_fattura, type='boolean', method=True,
            store=False, string="Congruente con fattura"),
        }

vendita_banco()
