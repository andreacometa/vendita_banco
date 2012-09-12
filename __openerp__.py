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

{
    'name': 'Vendita Banco',
    'version': '1.0',
    'category': 'POS',
    'description': """Modulo creato per venire incontro alle esigenze di chi ha bisogno di effettuare rapide vendite al banco.
    Il modulo è pensato in modo particolare per gli utenti italiano ed è perciò provvisto di alcuni automatismi molto utili""",
    'author': 'Apruzzese Francesco',
    'website': 'http://www.andreacometa.it',
    'license': 'AGPL-3',
    "active": False,
    "installable": True,
    "depends" : ['account', 'stock', 'l10n_it', 'l10n_it_sale', 'recupero_protocolli',],
    "update_xml" : [
        'stock/stock_view.xml',
        'vendita_banco/vendita_banco_view.xml',
        'security/vendita_banco_security.xml',
        'security/ir.model.access.csv',
        'partner/partner_view.xml',
        'vendita_banco/causali.xml',
        'wizard/wizard_genera_fatture_view.xml',
        'wizard/wizard_view.xml',
        'account/invoice_view.xml',
    ],
}
