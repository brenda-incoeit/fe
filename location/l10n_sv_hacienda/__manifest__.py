{
    "name": "Modulo Base para los Web Services de Hacienda",
    "version": "16.0.1",
    "category": "Localization/ElSalvador",
    "sequence": 14,
    "author": "Daniel Jove<daniel.jove@service-it.com.ar>",
    "license": "Other proprietary",
    "summary": "",
    "depends": [
        "base_sv",
        "l10n_sv",  # needed for CUIT and also demo data
        # "l10n_sv_dpto",  # needed for CUIT and also demo data
        "contacts",
        # TODO this module should be merged with l10n_ar_afipws_fe as the dependencies are the same
    ],
    # "external_dependencies": {"python": ["pyafipws", "OpenSSL", "pysimplesoap"]},
    "data": [
        "wizard/upload_certificate_view.xml",
        "wizard/res_partner_update_from_padron_wizard_view.xml",
        "views/afipws_menuitem.xml",
        "views/ir_cron.xml",        
        "views/afipws_certificate_view.xml",
        "views/afipws_certificate_alias_view.xml",
        "views/afipws_connection_view.xml",
        "views/res_config_settings.xml",
        "views/res_partner.xml",
        "views/res_company.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir.actions.url_data.xml",
        "data/ir.cron.xml",
    ],
    "demo": [
        "demo/certificate_demo.xml",
        "demo/parameter_demo.xml",
    ],
    "images": [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
