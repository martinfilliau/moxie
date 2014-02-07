OxPoints importer
=================

The OxPoints importer is using the RDF/XML representation of the full dataset of OxPoints,
and also requires the extension of OxPoints containing shapes of buildings as WKT (Well-Known Text).

The goal of Moxie is to provide a "simplified" view of OxPoints, easier to understand
from an end-user point of view. The following transformations have been done:

1. College/Hall/Department/Faculty have been merged with their **primary site** in one document
2. Some types have been regrouped (see table below)

Types mapping
-------------

The following table explains the transformation on types between OxPoints and Moxie.

======================= =======================
OxPoints type           Mapped type
======================= =======================
Building                Building
Carpark                 **University** carpark
College                 College
Department              Department
Division                Division
Faculty                 **Department**
Hall                    Hall
Library                 Library
Museum                  Museum
OpenSpace               **Not imported**
Outside                 **Not imported**
Place
Room                    Room
Site                    Site
Space                   Space
StudentGroup            **Not imported**
SubLibrary              SubLibrary
Unit                    **Department**
University              University
======================= =======================
