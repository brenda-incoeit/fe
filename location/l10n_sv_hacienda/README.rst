.. |company| replace:: Service-IT AR

.. |company_logo| image:: https://service-it.com.ar/web/image/res.company/1/logo?unique=88496f0
   :alt: ADHOC SA
   :target: https://www.service-it.com.ar

.. |icon| image:: https://service-it.com.ar/web/image/res.company/1/logo?unique=88496f0

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: Other-propietary

=========================================
Modulo Base para los Web Services de Hacienda
=========================================

Homologation / production:
--------------------------

First it search for a paramter "afip.ws.env.type" if exists and:

* is production --> production
* is homologation --> homologation

Else

Search for 'server_mode' parameter on conf file. If that parameter:

* has a value then we use "homologation",
* if no parameter, then "production"

Incluye:
--------

* Wizard para instalar los claves para acceder a las Web Services.
* API para realizar consultas en la Web Services desde OpenERP.

El módulo l10n_sv_hacienda permite a OpenERP acceder a los servicios del Hacienda a
travésde Web Services. Este módulo es un servicio para administradores y
programadores, donde podrían configurar el servidor, la autentificación
y además tendrán acceso a una API genérica en Python para utilizar los
servicios Hacienda.

Tenga en cuenta que estas claves son personales y pueden traer conflicto
publicarlas en los repositorios públicos.

Installation
============

To install this module, you need to:

#. Do this ...

Configuration
=============

To configure this module, you need to:

#. Go to ...

Usage
=====

To use this module, you need to:


Credits
=======

Images
------

* |company| |icon|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://service-it.com.ar.
