# Controle eerste testversie 0.1.0

Uitgevoerd op 30 oktober 2026 in een geïsoleerde tijdelijke Home Assistant-configuratie.

**Resultaat: 21 tests geslaagd.**

Omgeving: Python 3.12.14, Home Assistant Core 2024.12.5, pytest 9.2.0, pytest-asyncio 1.4.1.

## Afwijkingsherkenning en selectie — 20 controles

- W/kW/mW normaliseren; onbekende, onbeschikbare, niet-eindige, negatieve waarden en energie-eenheden afwijzen (8 gevallen).
- Verhoogd verbruik pas na twee meeturen bevestigen; afwijkende uren niet inleren.
- Verlaagd verbruik bevestigen en herstel herkennen.
- Een korte vermogenspiek geeft geen alarm.
- Een eerder waargenomen normale periodieke verbruikscyclus blijft binnen de bandbreedte.
- Uitval telt niet als nulverbruik en onderbreekt de bevestiging.
- Herstel uit opgeslagen profielen behoudt geschiedenis en overbrugt de downtime niet.
- Een volledige gesimuleerde leerweek met wisselend vermogen levert tijdgewogen uurgemiddelden op; vóór 7 dagen geen beoordeling.
- Een lange meetonderbreking wordt geen volledig meetuur.
- Netmeter, Nexus en PV overslaan; gewone apparaten, zonneboiler en verschillende kanalen behouden.
- Handmatig opnemen en uitsluiten, met voorrang voor uitsluiten.
- Duidelijke dubbele aliassen samenvoegen zonder een ander kanaal weg te laten.
- Eigen entiteiten, uitgeschakelde entiteiten en niet-vermogenssensoren overslaan.

## Werkelijke Home Assistant-lifecycle — 1 gecombineerde controle

De test gebruikt echte Home Assistant-code, geen nagemaakte HA-platforms:

- Laden vanuit de tijdelijke `custom_components`-map.
- Configuratiescherm zonder in te vullen velden en éénmalig toevoegen.
- Automatische selectie van een aanwezige vermogenssensor; P1 overslaan.
- Automatisch overzicht, algemene afwijkingssensor en apparaatstatus aanmaken.
- Een nieuw toegevoegde kW-sensor automatisch meenemen en naar W omrekenen.
- Een tweede installatie tegenhouden.
- Het optionele instellingenscherm openen, uitsluiten en herladen.
- Normaal afsluiten, opslaan, opnieuw laden en verwijderen inclusief opslagbestand.

Zeven deprecation-waarschuwingen kwamen uit externe Home Assistant-afhankelijkheden in de testomgeving. Geen testfouten.

## Nog te controleren in de praktijk

- Installatie op de actuele Home Assistant-versie van het huishouden.
- Minimaal een leerweek met echte sensorupdates en de bruikbaarheid van meldingen daarna.
- Selectie met de daadwerkelijke apparaatnamen, dubbele meetbronnen en firmwaregedrag.
- Meldingsweergave in de eigen app/browser; automatische installatie van telefoon-push is niet inbegrepen.
- HACS-validatie en hassfest zodra een echte repository met beheerder en project-URL bestaat.

De geslaagde tests bewijzen de geteste softwaregedragingen; ze zijn geen garantie voor foutloze apparaatherkenning of detectie bij ieder huishouden.
