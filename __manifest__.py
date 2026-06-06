{
    "name": "Órdenes de Lentes",
    "version": "17.0.1.0.0",
    "summary": "Control de fabricación de lentes (En espera → En proceso → Por entregar → Entregado)",
    "category": "Sales/Optics", 
    "author": "Christian Torres PeeWee",
    "license": "LGPL-3",
    "depends": ["base", "sale", "purchase", "mail", "portal", "product", "odoo_graduacion_paciente"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/lente_orden_views.xml", 
        "report/lente_orden_report.xml",
        "report/lente_orden_report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "Orden_de_lentes/static/src/css/lente_orden_flow.css",
        ],
    },
    "application": True,
    "installable": True,
}
