#!/usr/bin/env python
"""Structured ontology from Draper

Originally supplied:

Entity,State
hospit,overflow
clinic,overrun
medic system,overload
health system,overwhelm
treatment center,collaps
treatment unit,(cannot|could not|are not|struggl to) (cope|manage)
emerg room,(at|over|limited|shortag of|do not have) capac
icu,shortag of bed
health center,(bed|cot) in the (hallway|hall|corridor)
,crowd
,overcrowd
,close
,shut
,closure
,patient are (lie on|on) the floor

"""

ontology = {}
ontology['facilityterm'] = [
    'hospital',
    'clinic',
    'treatment center',
    'emergency room',
    'emergency department',
    'treatment unit',
    'treatment center',
    'health center',
    'icu',
    'intensive care unit',
    'OT',
    'OPD'
]
ontology['systemterm'] = [
    'medical system',
    'health system',
    'infrastructure',
    'health delivery system',
    'health staff'
]

ontology['problemterm'] = [
    'overflow',
    'overload',
    'overwhelm',
    'collapse',
    'crowd',
    'overcrowd',
    'over crowd',
    'close',
    'shut',
    'closure',
    'overrun',
    'swamp',
    'cease function',
    'ceased function',
    'meltdown',
    'breakdown',
    'struggle'
]

ontology['leftterms'] = [ 'facilityterm', 'systemterm' ]
ontology['rightterms'] = [ 'problemterm' ]

standalones = [
    '[cannot|could not|are not|struggle to] cope|manage',
    '[at|over|limited|shortage of|do not have] capacicty',
    'shortage of bed',
    'bed|cot in the hallway|hall|corridor',
    'patient be [lie on|on] the floor'
]


