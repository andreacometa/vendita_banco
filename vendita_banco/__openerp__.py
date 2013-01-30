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

{
    'name': 'Vendita Banco',
    'version': '1.0',
    'category': 'POS',
    'description': """Modulo creato per venire incontro alle esigenze di chi ha bisogno di effettuare rapide vendite al banco.
    Il modulo è pensato in modo particolare per gli utenti italiano ed è perciò provvisto di alcuni automatismi molto utili""",
    'author': 'www.andreacometa.it',
    'website': 'http://www.andreacometa.it',
    'license': 'AGPL-3',
    "active": False,
    "installable": True,
    "depends" : ['account', 'invoice_immediata_differita', 'stock', 'l10n_it', 'l10n_it_sale', 'recupero_protocolli','account_spesa'],
    "update_xml" : [
        'stock/stock_view.xml',
        'security/vendita_banco_security.xml',
        'security/ir.model.access.csv',
        'vendita_banco/vendita_banco_view.xml',
        'partner/partner_view.xml',
        'vendita_banco/causali.xml',
        'wizard/wizard_genera_fatture_view.xml',
        'wizard/wizard_raggruppa_documenti_view.xml',
        'wizard/wizard_view.xml',
        'account/invoice_view.xml',
        'vb_causali.xml',
        'vb_tipo_trasporto.xml',
    ],
}
