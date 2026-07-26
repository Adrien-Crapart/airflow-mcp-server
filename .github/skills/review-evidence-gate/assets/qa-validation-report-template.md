# Rapport QA Validation Template

RAPPORT DE VALIDATION QUALITE
==============================
Ticket JIRA             : {{CLE_TICKET}} - {{TITRE}}
Date / heure du passage : {{DATE_HEURE}}
Environnement teste     : {{TESTDEV / PREPROD / PRODUCTION}}
Agent / testeur         : {{NOM}}

1. SYNTHESE
- Taux de completude du ticket       : {{X}} / 12 elements presents
- Taux de couverture des cas de test : {{X}} %
- Nombre d alertes de completude     : {{N}}
- Nombre d anomalies detectees       : {{N}}
- Recommandation finale              : {{GO / NO-GO / GO CONDITIONNEL}}

2. DETAIL PAR SECTION
| Section                         | Statut global (✅/❌/⚠️/➖) | Points bloquants |
|---------------------------------|-----------------------------|------------------|
| 3. Completude du ticket         |                             |                  |
| 5. Qualite technique            |                             |                  |
| 6. Qualite metier/fonctionnelle |                             |                  |
| 7. Qualite des donnees          |                             |                  |
| 8. Qualite API                  |                             |                  |
| 9. Cas de test                  |                             |                  |
| 10.x Environnement teste        |                             |                  |

3. ALERTES DE COMPLETUDE
- {{ALERTE_1}}
- {{ALERTE_2}}

4. ANOMALIES DETECTEES
[SEVERITE] {{TITRE_COURT}}
- Preuve: {{fichier:ligne ou cellule}}
- Reference: {{spec, critere, regle, standard}}
- Risque: {{impact si non corrige}}
- Recommandation: {{action concrete et testable}}

[SEVERITE] {{TITRE_COURT_2}}
- Preuve: {{fichier:ligne ou cellule}}
- Reference: {{spec, critere, regle, standard}}
- Risque: {{impact si non corrige}}
- Recommandation: {{action concrete et testable}}

5. ACTIONS CORRECTIVES AVANT PROCHAINE ETAPE
- {{Action 1 - responsable - delai}}
- {{Action 2 - responsable - delai}}

6. PROCHAINE ETAPE
- {{Rejouer sur environnement suivant / Corriger et rejouer / Cloturer ticket}}

## Regles de decision
- Si un BLOQUANT est non resolu: NO-GO
- Si une preuve critique manque: Non testable - preuve indisponible
- Toute conclusion doit etre traçable aux preuves ci-dessus
