# WattWatch — eerste testversie 0.1.0

Automatisch veranderingen in het stroomverbruik van apparaten volgen in Home Assistant.

## Eenmalig installeren

1. Pak dit ZIP-bestand uit op een computer. Kopieer de map **wattwatch** die binnen **custom_components** staat naar de map **custom_components** in jouw Home Assistant-configuratiemap. Maak die laatste map aan als die nog niet bestaat. Het resultaat is `/config/custom_components/wattwatch/manifest.json` (op HA OS).
2. Herstart Home Assistant volledig.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen → WattWatch**. Open de integratie en klik op **Verzenden** om te starten.

Dat is alles voor deze testversie. Er hoeft geen YAML aangepast te worden. Helpers, Node-RED, MQTT, een abonnement of een cloudaccount zijn niet nodig. Er moeten wel al vermogenssensoren van je apparaten in Home Assistant aanwezig zijn. WattWatch installeert geen koppelingen voor slimme stekkers en kan het stroomverbruik niet uit een gewone aan/uitknop afleiden.

WattWatch is ook te installeren met HACS: open **HACS → Integraties → ⋮ → Aangepaste repositories**, voeg `https://github.com/Kprins1983/Wattwatch` toe als type **Integratie**, installeer WattWatch en herstart Home Assistant. Daarna kun je verder met stap 3 hierboven.

## Wat gebeurt er vanzelf?

- Iedere minuut bestaande en nieuwe vermogenssensoren herkennen (W, kW of mW).
- Veel herkenbare netmeters, opwekkers, batterijen en totaalsensoren overslaan.
- Voor ieder gevonden vermogenskanaal een status aanmaken.
- Leerdata lokaal opslaan en na een herstart weer gebruiken.
- Een automatisch overzicht op de **apparaatpagina van WattWatch** tonen.
- Bij een bevestigde afwijking een melding binnen Home Assistant plaatsen.

Er wordt geen aparte Lovelace-dashboardpagina geïnstalleerd. Het overzicht gebruikt de ingebouwde apparaatpagina: open de integratie WattWatch en vervolgens het apparaat WattWatch. Daar staan **Gevolgde apparaten**, **Afwijkend verbruik** en de afzonderlijke statussen. Sommige namen worden door Home Assistant vertaald naar de ingestelde taal. Nederlandse en Engelse teksten zijn inbegrepen.

## Eerst leren

De status begint met **Bezig met leren**. De eerste beoordeling vraagt minimaal **7 dagen** sinds de eerste meting, **120 bruikbare meeturen** in de bewaarde geschiedenis en voldoende referentiemetingen rond hetzelfde lokale tijdstip op minimaal 5 eerdere dagen. Bij ontbrekende gegevens kan het langer duren. De voortgang staat bij het betreffende apparaat in het attribuut `learning_percent`.

WattWatch leest eenmaal per minuut het actuele vermogen. Voor ieder verstreken klokuur wordt een tijdgewogen gemiddelde berekend. Een meetuur telt alleen mee met minstens 45 minuten dekking. Onbekende waarden, negatieve waarden en lange onderbrekingen tellen niet als nulverbruik. De bestaande Recorder-geschiedenis wordt in deze versie niet ingelezen.

## Wanneer volgt een melding?

Twee opeenvolgende bruikbare klokuren moeten buiten de gebruikelijke bandbreedte liggen, in dezelfde richting. De vergelijking gebruikt eerdere dagen op ongeveer hetzelfde lokale uur (hetzelfde uur en het uur ervoor/erna). Daardoor komt een melding doorgaans pas na ongeveer 2 tot 3 uur aanhoudend afwijkend verbruik. Een korte piek is niet het doel van deze monitor.

Per apparaat geldt een meldingspauze van 24 uur. Dezelfde melding wordt daarna bijgewerkt in plaats van gestapeld. Na een normaal beoordeeld meetuur verdwijnt die melding vanzelf. Na een herstart begint de bevestiging van twee uur opnieuw; de referentiegeschiedenis blijft behouden.

Dit is een eenvoudige, transparante statistische detector. Er is geen cloud-AI. De monitor houdt in deze versie geen rekening met buitentemperatuur, werkdag/weekend of het gekozen apparaatprogramma. Een afwijking is geen vastgestelde storing. Nieuwe gewoontes, vakanties of ander weer kunnen ook een signaal veroorzaken. Apparaten met grote normale variatie krijgen een brede bandbreedte; kleine afwijkingen kunnen daardoor onopgemerkt blijven.

## Alleen als een uitzondering nodig is

Via **Configureren** bij de integratie kun je:

- Meldingen in Home Assistant uitschakelen.
- Sensoren uitsluiten die toch geen afzonderlijk apparaat zijn.
- Sensoren alsnog opnemen die ten onrechte automatisch zijn overgeslagen.

Uitsluiten heeft voorrang. Sensoren moeten geschikte eenheden houden; opnemen maakt van een kWh-sensor geen vermogenssensor.

Automatisch filteren is niet foutloos: Home Assistant heeft geen universeel veld dat zegt of een vermogenssensor een heel huis, een batterij of een enkel apparaat meet. Onherkenbaar benoemde totaalsensoren kunnen daarom toch worden meegenomen. Ook dubbele sensoren zijn niet altijd automatisch herkenbaar. Alleen duidelijke gelijknamige aliassen op hetzelfde geregistreerde apparaat worden samengevoegd. Meerdere kanalen van één apparaat blijven afzonderlijk beschikbaar.

**De eerste versie meldt binnen Home Assistant. Telefoon-pushmeldingen zijn nog niet ingebouwd.** Alle benodigde onderdelen voor deze functies zitten in het pakket; er hoeft geen meldingsautomatisering te worden gemaakt.

## Opslag, privacy en verwijderen

De laatste maximaal 21 dagen aan bruikbare uurgemiddelden worden lokaal bewaard. Er wordt niets door WattWatch naar internet verstuurd. Opslag gebeurt circa iedere 5 minuten; bij normale herlading wordt de laatste stand ook opgeslagen. Bij stroomuitval kan het laatste onopgeslagen deel verloren gaan. Het lopende, nog niet voltooide meetuur wordt na een herstart opnieuw opgebouwd.

Verwijder je de integratie via Apparaten & diensten, dan verwijdert WattWatch de eigen opgeslagen leergegevens. Eerder door Home Assistant Recorder bewaarde entiteitsgeschiedenis volgt de normale bewaartermijn van Home Assistant. Om alle patronen opnieuw te leren kun je de integratie verwijderen en opnieuw toevoegen.

## Status van deze versie

Dit is een **testversie**, geen al bewezen product voor alle huishoudens. De geautomatiseerde controles staan in `TESTRESULTATEN.md`. In een geïsoleerde omgeving is Home Assistant **2024.12.5** gebruikt met Python **3.12.14**. Op de huidige Home Assistant-versie van de gebruiker en met echte apparaten moet nog een praktijktest plaatsvinden. De minimale versie in `hacs.json` is 2024.12.0; niet elke tussenliggende of latere versie is afzonderlijk getest.

Zie `README.md` voor installatie via HACS en informatie voor ontwikkelaars.
